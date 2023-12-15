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
        # ['Telefono_2','Telefono_3','Telefono_4','Telefono_5','Telefono_6','Telefono_7','Telefono_8','Telefono_9']
        self.OTROS = tel_otros
        self.SEPARADOR = col_separador  # ['Ejecutivo'
        # self.OTRO_DISTINTOR =['']
        self.necesario = self.DNI + self.NOMBRE + self.SEPARADOR + self.MASIVO + self.OTROS

        self.sep_numeros = sep_numeros
        # self.TIPO = tipo  # si es M o R segun sea amsivo o otro
        self.ENCABEZADO_RESULTADO = ["Nombre", "Apellido", "Trabajo"]
        self.RESULTADO_SUBIDA = pd.DataFrame(columns=self.ENCABEZADO_RESULTADO)

        self.RESULTADOS = dict()

    def build_datasheet(self) -> None:

        df_contacts = self._get_df_to_work_with()
        df_contacts = self.separa_masivo(df_contacts)

        self.df_contacts = self.df_contacts.melt(id_vars=self.DNI + self.NOMBRE + self.SEPARADOR)

        self.df_contacts.dropna(axis='index', inplace=True)

        self.df_contacts["Nombre"] = self.df_contacts["variable"] + " " + self.df_contacts["Mat. Unica"]
        self.df_contacts.drop(['Mat. Unica', 'variable'], inplace=True, axis=1)

        self.df_contacts = self.df_contacts.rename(columns={'Razon Social': 'Apellido', 'value': 'Trabajo'})
        self.df_contacts = self.df_contacts.reindex(columns=['Nombre', 'Apellido', 'Trabajo', 'Ejecutivo'])

        for ejecutivo, datos in self.df_contacts.groupby(self.df_contacts[self.SEPARADOR[0]]):
            self.RESULTADOS[ejecutivo] = datos[['Nombre', 'Apellido', 'Trabajo']].copy()

        self.Guardar_resultados()

    def _get_df_to_work_with(self) -> pd.DataFrame:
        df = self._get_only_required_columns_from_uploaded_data()
        df = self._rename_df_columns(df)
        return df

    def _get_only_required_columns_from_uploaded_data(self) -> pd.DataFrame:
        return self.df_datos[self.necesario]

    def _rename_df_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        renaming_dict = {column: f'RIESGO {index}' for index, column in enumerate(self.OTROS, 1)}
        renaming_dict[self.MASIVO[0]] = 'MASI'
        return df.rename(columns=renaming_dict)

    def separa_masivo(self, df: pd.DataFrame) -> pd.DataFrame:
        'separa los masivos dobles y ademas rellena los ejecutivos vacios'
        masivos = df['MASI'].str.split('-', expand=True)
        # pepe.to_csv('muestra_3.csv', sep =';')

        # masivos

        renombre = {x: f'MASI {i}' for i, x in enumerate(list(masivos.columns), 1)}
        masivos = masivos.rename(columns=renombre)
        df = pd.concat([df, masivos], axis=1)

        df.drop('MASI', inplace=True, axis=1)
        df['Ejecutivo'].fillna('sin ejecutivo', inplace=True)
        return df

    def Guardar_resultados(self):
        ruta = 'resultados temporales'
        if os.path.isdir(ruta):

            os.chdir(ruta)

            try:
                # vaciar directorio archivos temproales
                for file in os.listdir():
                    os.remove(file)

            finally:
                os.chdir('..')

        else:
            os.mkdir(ruta)

        # escribir archivos
        os.chdir(ruta)
        try:
            # escerib
            with zipfile.ZipFile('Bases Google.zip', 'w') as csv_zip:
                for ejec, data in self.RESULTADOS.items():
                    csv_zip.writestr(f"{ejec}.csv", pd.DataFrame(data).to_csv(sep=';', encoding='ANSI', index=False))

        finally:
            os.chdir('..')
