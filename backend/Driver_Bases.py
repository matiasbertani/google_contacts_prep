import pandas as pd
import zipfile
import os


class GoogleContactsDataBuilder:

    def __init__(self, base, col_dni, razon_social, tel_masivo, tel_otros, col_separador, sep_numeros='-') -> None:

        self.df_datos = base
        self.PLANILLA_DATOS = base
        self.DNI = col_dni  # ['Mat. Unica']
        self.NOMBRE = razon_social  # ['Razon Social']
        self.MASIVO = tel_masivo  # ['Telefono_1']
        self.OTROS = tel_otros  # ['Telefono_2','Telefono_3','Telefono_4','Telefono_5','Telefono_6','Telefono_7','Telefono_8','Telefono_9']
        self.SEPARADOR = col_separador  # ['Ejecutivo'
        # self.OTRO_DISTINTOR =['']
        self.necesario = self.DNI + self.NOMBRE + self.SEPARADOR + self.MASIVO + self.OTROS

        self.sep_numeros = sep_numeros
        # self.TIPO = tipo  # si es M o R segun sea amsivo o otro
        self.ENCABEZADO_RESULTADO = ["Nombre", "Apellido", "Trabajo"]
        self.RESULTADO_SUBIDA = pd.DataFrame(columns=self.ENCABEZADO_RESULTADO)

        self.RESULTADOS = dict()

    def __renombrar(self):
        'Elige de los datos solo lo necesario y reescribe los nombre sque le sirven '
        df_fono = self.df_datos[self.necesario]
        renombre = {x: f'RIESGO {i}' for i, x in enumerate(self.OTROS, 1)}
        renombre[self.MASIVO[0]] = 'MASI'
        # renombre
        self.df_datos = df_fono.rename(columns=renombre)

    def separa_masivo(self):
        'separa los masivos dobles y ademas rellena los ejecutivos vacios'
        masivos = self.df_datos['MASI'].str.split('-', expand=True)
        # pepe.to_csv('muestra_3.csv', sep =';')

        # masivos

        renombre = {x: f'MASI {i}' for i,x in enumerate(list(masivos.columns), 1)}
        masivos = masivos.rename(columns=renombre)
        self.df_datos = pd.concat([self.df_datos, masivos], axis=1)

        self.df_datos.drop('MASI', inplace=True, axis=1)
        self.df_datos['Ejecutivo'].fillna('sin ejecutivo', inplace= True)

    def build_datasheet(self) -> None:

        self.__renombrar()   
        self.separa_masivo()

        self.df_datos = self.df_datos.melt(id_vars=self.DNI + self.NOMBRE + self.SEPARADOR)

        self.df_datos.dropna(axis='index', inplace=True)

        self.df_datos["Nombre"] =  self.df_datos["variable"] + " " + self.df_datos["Mat. Unica"]
        self.df_datos.drop(['Mat. Unica','variable'], inplace=True, axis=1)

        self.df_datos = self.df_datos.rename(columns={'Razon Social': 'Apellido','value':'Trabajo'})
        self.df_datos = self.df_datos.reindex(columns=['Nombre','Apellido','Trabajo','Ejecutivo'])

        for ejecutivo, datos in self.df_datos.groupby(self.df_datos[self.SEPARADOR[0]]):
            self.RESULTADOS[ejecutivo] = datos[['Nombre','Apellido','Trabajo']].copy()

        self.Guardar_resultados()

    def Guardar_resultados(self):
        ruta ='resultados temporales'
        if os.path.isdir(ruta):

            os.chdir(ruta)

            try:
                # vaciar directorio archivos temproales
                for file in os.listdir():
                    os.remove(file)

            finally:
                os.chdir('..')

        else: os.mkdir(ruta)     

        # escribir archivos
        os.chdir(ruta)
        try:
            # escerib
            with zipfile.ZipFile('Bases Google.zip', 'w') as csv_zip:
                for ejec, data in self.RESULTADOS.items():
                    csv_zip.writestr(f"{ejec}.csv", pd.DataFrame(data).to_csv(sep=';', encoding='ANSI', index=False))

        finally:
            os.chdir('..')
