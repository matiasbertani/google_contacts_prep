from pathlib import Path

import os
import traceback
import zipfile

import pandas as pd


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

        self.results_path = Path() / 'results'

    def build_datasheet(self) -> None:

        df_contacts = self._get_df_to_work_with()
        df_contacts = self._split_main_phones(df_contacts)
        df_contacts['Ejecutivo'].fillna('sin ejecutivo', inplace=True)
        df_contacts = df_contacts.melt(id_vars=self.DNI + self.NOMBRE + self.SEPARADOR)

        df_contacts.dropna(axis='index', inplace=True)

        df_contacts["Nombre"] = df_contacts["variable"] + " " + df_contacts["Mat. Unica"]
        df_contacts.drop(['Mat. Unica', 'variable'], inplace=True, axis=1)

        df_contacts = df_contacts.rename(columns={'Razon Social': 'Apellido', 'value': 'Trabajo'})
        df_contacts = df_contacts.reindex(columns=['Nombre', 'Apellido', 'Trabajo', 'Ejecutivo'])

        for ejecutivo, datos in df_contacts.groupby(df_contacts[self.SEPARADOR[0]]):
            self.RESULTADOS[ejecutivo] = datos[['Nombre', 'Apellido', 'Trabajo']].copy()

        self._save_results()

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

    def _split_main_phones(self, df: pd.DataFrame) -> pd.DataFrame:

        splitted_main_phones = df['MASI'].str.split('-', expand=True)

        renaiming_dict = {x: f'MASI {i}' for i, x in enumerate(list(splitted_main_phones.columns), 1)}
        splitted_main_phones = splitted_main_phones.rename(columns=renaiming_dict)

        df = pd.concat([df, splitted_main_phones], axis=1)
        df.drop('MASI', inplace=True, axis=1)

        return df

    def _save_results(self) -> None:
        if not os.path.isdir(self.results_path):
            os.mkdir(self.results_path)

        self._clean_result_dir()
        self._write_results()

    def _clean_result_dir(self) -> None:
        try:
            for file in os.listdir(self.results_path):
                os.remove(self.results_path / file)
        except Exception:
            print(traceback.format_exc())

    def _write_results(self) -> None:

        try:
            with zipfile.ZipFile('Bases Google.zip', 'w') as csv_zip:
                for ejec, data in self.RESULTADOS.items():
                    csv_zip.writestr(
                        self.results_path / f"{ejec}.csv",
                        pd.DataFrame(data).to_csv(sep=';', encoding='ANSI', index=False),
                    )

        except Exception:
            print(traceback.format_exc())
