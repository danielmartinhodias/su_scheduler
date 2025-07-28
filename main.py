import streamlit as st
import os
import pandas as pd
import re
import tabula
import datetime
from datetime import timedelta
from caldav import DAVClient, Calendar


st.header("Turnos de SU CHUSJ")

def extract_shift_code_times(df):
    shift_dict = {}
    excluded_codes = {'LF', '5000', 'PS'}

    for idx, row in df.iterrows():
        row_values = row.dropna().astype(str).tolist()

        # If row has an odd number of items, drop the first one (usually a label like 'Espaço', 'Lf', etc.)
        if len(row_values) % 2 != 0:
            row_values = row_values[1:]

        i = 0
        while i < len(row_values) - 1:
            code = row_values[i].strip().upper()
            desc = row_values[i + 1].strip()

            match = re.search(r'(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})', desc)
            if match and code not in excluded_codes and not code.isdigit():
                shift_dict[code] = f"{match.group(1)} - {match.group(2)}"

            i += 2

    return shift_dict


uploaded_file = st.file_uploader("Faz upload do plano mensal do SU (PDF)", type=["pdf"])
if uploaded_file is not None:
    # To read file as bytes:
    filename = uploaded_file.name
    ano=int(filename[:4])
    mes=int(filename[5:7])
    st.write("Plano SU de ", mes," de ", ano)
    
    save_folder = "./"
    
    # Create the folder if it doesn't exist
    os.makedirs(save_folder, exist_ok=True)
    
    # Define full path with filename
    save_path = os.path.join(save_folder, uploaded_file.name)
    with open(f"./{uploaded_file.name}", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"Saved PDF file: {save_path}")

  # get shifts codes
    tables = tabula.read_pdf(save_path, pages='all', multiple_tables=True, pandas_options={"header": None})
    
    df_shifts1 = tables[0]
    df_shifts2=tables[1]  # or whichever has your schedule
    df_shifts=pd.concat((df_shifts1.iloc[1:], df_shifts2[1:]), ignore_index=True)
    df_staff_count = tables[2] 
    df_codes2=tables[3]
    # print (df_shifts)
    dict_todos_codigos = extract_shift_code_times(df_codes2)

  # get numero mecanografico
    # df['Unnamed: 0']=df['Unnamed: 0'].fillna(0).astype(int)

    # # print(df[df["Unnamed: 1"] == "DANIEL MARTINHO FERREIRA DIAS "])

    numero = st.text_input("Número mecanográfico:")
    if numero:
      numero=int(numero)

      new_dict={
      }
      df_shifts.columns=df_shifts.iloc[0]
      df_shifts.columns.values[0]="n_mecanografico"
      df_shifts.columns.values[1]="nome"
      df_shifts['n_mecanografico']=df_shifts['n_mecanografico'].fillna(0).astype(int)

      new_cols = []
      seen_31 = False

      for col in df_shifts.columns:
        # Rule 1: Rename first '31' to '31.1'
        if col == '31' and not seen_31:
            new_cols.append('31.1')
            seen_31 = True
        # Rule 2: If it starts with '1-' (like '1-ago'), rename to '1'
        elif re.match(r'^\d+-', str(col)):
          new_cols.append(col.split('-')[0])
        else:
            new_cols.append(col)

      df_shifts.columns = new_cols

      # st.write("df_shifts: ", df_shifts)

      for item in df_shifts.columns[2:]:
        key=item
        value=df_shifts[df_shifts['n_mecanografico'] == numero][item].values[0]
        if pd.isna(value):
            continue
        else:
            # print(key, value)
            new_dict[key]=value

      # st.write ("new_dict", new_dict)

      last_dict={k: dict_todos_codigos[v] for k,v in new_dict.items()}

      st.write("Turnos:")
      st.write("Os turnos são:", last_dict)


      def calcular_horas_entre_intervalo(intervalo):
        inicio_str, fim_str = intervalo.split(" - ")
        formato = "%H:%M"
        hora_inicio = datetime.datetime.strptime(inicio_str, formato)
        hora_fim = datetime.datetime.strptime(fim_str, formato)

        # Ajusta se o horário de fim for no dia seguinte
        if hora_fim < hora_inicio:
          hora_fim += timedelta(days=1)

        diferenca = hora_fim - hora_inicio
        return diferenca.total_seconds() / 3600
      
      hours_dict={}
      for key in last_dict:
        hours_dict[key]=calcular_horas_entre_intervalo(last_dict[key])

      count=0
      for key in hours_dict.keys():
        count+=hours_dict[key]
      st.write(int(count), "horas no mês", "com uma Média de", round(count/4), "horas/semana")


      events = []

      for key, time_range in last_dict.items():
          # Extract day (may include '-jul' or just be a number)
          match = re.search(r'(\d+)', key)
          if not match:
              continue

          day = int(match.group(1))
          if '.1' in key:
            mes = mes - 1  # July
          else:
            mes = mes      # August

          # Extract start and end times
          start_str, end_str = time_range.split(" - ")
          start_hour, start_minute = map(int, start_str.split(":"))
          end_hour, end_minute = map(int, end_str.split(":"))

          # Create start datetime
          start_dt = datetime.datetime(ano, mes, day, start_hour, start_minute)

          # Create end datetime (add a day if past midnight)
          end_dt = datetime.datetime(ano, mes, day, end_hour, end_minute)
          if end_dt <= start_dt:
              end_dt += timedelta(days=1)

          events.append((start_dt, end_dt))

      # Output the events


      ### CALENDÁRIO ####
      status = st.empty()
      status.write("A enviar dados para o calendário pré-configurado...")

      # Your iCloud credentials
      ICLOUD_USERNAME = "dm_dias@icloud.com"
      ICLOUD_APP_SPECIFIC_PASSWORD = "iufn-lkek-vyqc-xvdt"
      CALENDAR_NAME = "Trabalho"


    # Connect to iCloud CalDAV
      client = DAVClient(
          url="https://caldav.icloud.com/",
          username=ICLOUD_USERNAME,
          password=ICLOUD_APP_SPECIFIC_PASSWORD
      )

      principal = client.principal()
      calendars = principal.calendars()

      # 🔍 Find the calendar by name
      calendar = next((cal for cal in calendars if cal.name == CALENDAR_NAME), None)

      if not calendar:
          raise Exception(f"Calendar named '{CALENDAR_NAME}' not found.")

      # Set your event details

      # st.write("events", events)

      # date_ranges = [
      #   [eval(start, {"datetime": datetime}), eval(end, {"datetime": datetime})]
      #   for start, end in events
      #   ]
      date_ranges = []
      for start, end in events:
        date_ranges.append((start,end))

        # [eval(start, {"datetime": datetime}), eval(end, {"datetime": datetime})]
        # for start, end in events
        # ]
      for start, end in date_ranges:
        event_text = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Your Script//EN
BEGIN:VEVENT
UID:{start.timestamp()}@example.com
DTSTAMP:{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{start.strftime('%Y%m%dT%H%M%S')}
DTEND:{end.strftime('%Y%m%dT%H%M%S')}
SUMMARY:SU-CHUSJ (auto)
DESCRIPTION:Este vai ser um dia de trabalho, mas vai correr bem :)
END:VEVENT
END:VCALENDAR
"""
          
        calendar.add_event(event_text)
        # st.write(f"Adicionado turno de dia {str(start)[8:-8]} ao calendário")
        
      status.success ("Turnos agendados no calendário :)")


