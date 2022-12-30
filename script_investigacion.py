"""
@author: Alex Terreros
"""
import pandas as pd
from bs4 import BeautifulSoup
from progress.bar import ChargingBar
import urllib.request

def req(url):
    try: 
        with urllib.request.urlopen(url) as response:
            return response.read()
    except:
        print("Error en la consulta.")
        pass

def link(url, num):
    data = pd.DataFrame()
    #Hace peticion a cada link 
    html = req(url)

    #listas para almacenar datos
    names_list = []
    institutions_list = []
    links_list = []

    #Pasa el html y lo parsea para que sea mas legible
    soup = BeautifulSoup(html, 'html.parser')
    names = soup.find_all("h3", class_="gs_ai_name")
    institutions = soup.find_all("div", class_="gs_ai_aff")

    for name in names:
        a_eti = name.find('a')
        links_list.append(a_eti['href'])
        nombre = a_eti.get_text().split("(")
        names_list.append(nombre[0])


    for institution in institutions:
        institutions_list.append(institution.get_text())

    i = 0

    bar = ChargingBar('Descargando de link '+str(num)+': ', max=len(links_list))

    for link in links_list:
        datos_by_user = [0,0,0,0,0,0]
        html_by_user = req('https://scholar.google.com'+link)
        soup_by_user = BeautifulSoup(html_by_user, 'html.parser')
        table_by_user = soup_by_user.find("table")
        datos_citas = table_by_user.find_all("td", class_="gsc_rsb_std")
        index = 0
        for dato in datos_citas:
            datos_by_user[index] = dato.get_text()
            index = index + 1
        
        #Citas de 2020 - 2021 - 2022
        datos_citas_last_years = [0,0,0]
        citas_all_years = []
        citas_last_years = soup_by_user.find_all("span", class_="gsc_g_al")
        for citas in citas_last_years:
            citas_all_years.append(citas.get_text())

        num_years = len(citas_all_years)
        if num_years > 0:
            datos_citas_last_years[2] = citas_all_years[num_years - 1]
            datos_citas_last_years[1] = citas_all_years[num_years - 2]
            datos_citas_last_years[0] = citas_all_years[num_years - 3]

        #Articulos disponibles y no disponibles
        try: 
            num_art_avia = soup_by_user.find(class_="gsc_rsb_m_a").get_text()
            num_art_not_avia = soup_by_user.find(class_="gsc_rsb_m_na").get_text()
        except:
            num_art_avia = "0"
            num_art_not_avia = "0"

        if num_art_avia != None:
            num = num_art_avia.split(" ")
            num_art_avia = num[0]
        
        if num_art_not_avia != None:
            num = num_art_not_avia.split(" ")
            num_art_not_avia = num[0]

        data_for_df = {
            "nombre": pd.Series(names_list[i]),
            "institucion": pd.Series(institutions_list[i]),
            "articulos disponibles": pd.Series(int(num_art_avia)),
            "articulos no disponibles": pd.Series(int(num_art_not_avia)),
            "citas 2020": pd.Series(int(datos_citas_last_years[0])),
            "citas 2021": pd.Series(int(datos_citas_last_years[1])),
            "citas 2022": pd.Series(int(datos_citas_last_years[2])),
            "citas totales": pd.Series(int(datos_by_user[0])),
            "citas desde 2017": pd.Series(int(datos_by_user[1])),
            "h-index": pd.Series(int(datos_by_user[2])),
            "h-index desde 2017": pd.Series(int(datos_by_user[3])),
            "i10-index": pd.Series(int(datos_by_user[4])),
            "i10-index desde 2017": pd.Series(int(datos_by_user[5])),
            "link": pd.Series("https://scholar.google.com"+link)
        }
        
        df_by_user = pd.DataFrame(data_for_df)
        data = pd.concat([data, pd.DataFrame.from_records(df_by_user)], ignore_index = True)
        i = i + 1
        bar.next()

    bar.finish()
    return data


def main():
    #Inicializa el dataframe con pandas
    allData = pd.DataFrame()

    read_links = pd.read_csv("links.csv", index_col=0)

    print("Iniciando descarga de Google Scholar...")
    num = 1
    for url in read_links.index:
        print("Numero de links: " + str(num) + "/" + str(len(read_links.index)))
        func_data = link(url, num)
        allData = pd.concat([allData, pd.DataFrame.from_records(func_data)], ignore_index = True)
        num = num + 1

    #Exportar en excel los resultados
    allData.to_excel("data_google_scholar.xlsx", index=False, header=True)

    print(allData)

if __name__ == "__main__":
    main()