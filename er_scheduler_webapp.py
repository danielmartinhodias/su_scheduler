import os
import streamlit as st
from io import StringIO
import datetime
from caldav import DAVClient, Calendar
import re
import pandas as pd
import convertapi
import datetime
from datetime import timedelta



st.header("SU CHUSJ")

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

    convertapi.api_credentials = '0xmNJLnevpFAIWDCMbWyrucfDT0vysr2'
    convertapi.convert('xlsx', {
        'File': save_path
    }, from_format = 'pdf').save_files(save_folder)

    print (save_path)
    df = pd.read_excel(f'{save_path[:-3]}xlsx', sheet_name='Table 1')
    df['Unnamed: 0']=df['Unnamed: 0'].fillna(0).astype(int)

    # print(df[df["Unnamed: 1"] == "DANIEL MARTINHO FERREIRA DIAS "])

    numero = st.text_input("Número mecanográfico:")
    if numero:
      numero=int(numero)


      new_dict={
      }

      for item in df.columns[2:]:
        key=item
        value=df[df['Unnamed: 0'] == numero][item].values[0]
        if pd.isna(value):
            continue
        else:
            print(key, value)
            new_dict[key]=value

        print ("new_dict")
        # print (new_dict)

      df_codigos = pd.read_excel(f'{save_path[:-3]}xlsx', sheet_name='Table 2', header=None)
      df_codigos=df_codigos.fillna("")
      all_text=' '.join(df_codigos.astype(str).values.flatten())



      pattern = r'(\b[A-Z0-9]+)\s+[^\(]*\((\d{2}:\d{2} - \d{2}:\d{2})\)'
      matches = re.findall(pattern, all_text)
      dict_result = dict(matches)
      # print(dict_result)

      last_dict={k: dict_result[v] for k,v in new_dict.items()}

      st.write("Turnos:")
      st.write(last_dict)


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

      events=[["datetime.datetime(2025, 7, 1, 8, 0)","datetime.datetime(2025, 7, 1, 16, 0)"],["datetime.datetime(2025, 7, 3, 14, 0)","datetime.datetime(2025, 7, 4, 0, 0)"],["datetime.datetime(2025, 7, 8, 8, 0)","datetime.datetime(2025, 7, 8, 16, 0)"],["datetime.datetime(2025, 7, 13, 15, 0)","datetime.datetime(2025, 7, 14, 1, 0)"],["datetime.datetime(2025, 7, 14, 14, 0)","datetime.datetime(2025, 7, 15, 2, 0)"],["datetime.datetime(2025, 7, 19, 12, 0)","datetime.datetime(2025, 7, 20, 0, 0)"],["datetime.datetime(2025, 7, 20, 14, 0)","datetime.datetime(2025, 7, 20, 20, 0)"],["datetime.datetime(2025, 7, 21, 8, 0)","datetime.datetime(2025, 7, 21, 14, 0)"],["datetime.datetime(2025, 7, 25, 18, 0)","datetime.datetime(2025, 7, 26, 2, 0)"]]

      date_ranges = [
          [eval(start, {"datetime": datetime}), eval(end, {"datetime": datetime})]
          for start, end in events
      ]

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