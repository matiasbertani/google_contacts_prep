from pathlib import Path

import os
import traceback
import zipfile

import pandas as pd


class GoogleContactsDataBuilder:

    def __init__(
        self,
        uploaded_datesheet: pd.DataFrame,
        identifier_column: list,
        full_name_column: list,
        main_phones_columns: list,
        other_phones_columns: list,
        column_to_group_by: list,
        main_phones_separator: str = '-',
    ) -> None:

        self.uploaded_datesheet = uploaded_datesheet

        self.identifier_column = identifier_column
        self.full_name_column = full_name_column
        self.main_phones_column = main_phones_columns
        self.other_phones_columns = other_phones_columns
        self.column_to_group_by = column_to_group_by

        self.main_phones_separator = main_phones_separator
        self.results_dict = dict()
        self.results_path = Path() / 'results'

    def build_datasheet(self) -> None:

        df_contacts = self._get_df_to_work_with()
        df_contacts = self._split_main_phones(df_contacts)
        df_contacts = df_contacts.melt(
            id_vars=self.identifier_column + self.full_name_column + self.column_to_group_by
        )

        df_contacts.dropna(axis='index', inplace=True)

        df_contacts["Nombre"] = df_contacts["variable"] + " " + df_contacts["Mat. Unica"]
        df_contacts.drop(['Mat. Unica', 'variable'], inplace=True, axis=1)

        df_contacts = df_contacts.rename(columns={'Razon Social': 'Apellido', 'value': 'Trabajo'})
        df_contacts = df_contacts.reindex(columns=['Nombre', 'Apellido', 'Trabajo', 'Ejecutivo'])

        for ejecutivo, datos in df_contacts.groupby(df_contacts[self.column_to_group_by[0]]):
            self.results_dict[ejecutivo] = datos[['Nombre', 'Apellido', 'Trabajo']].copy()

        self._save_results()

    def _get_df_to_work_with(self) -> pd.DataFrame:
        df = self._get_only_required_columns_from_uploaded_data()
        df = self._rename_df_columns(df)
        df[self.column_to_group_by].fillna(f'Sin {self.column_to_group_by}', inplace=True)
        return df

    def _get_only_required_columns_from_uploaded_data(self) -> pd.DataFrame:
        return self.uploaded_datesheet[self._required_columns]

    @property
    def _required_columns(self) -> list:
        return (
            self.identifier_column
            + self.full_name_column
            + self.column_to_group_by
            + self.main_phones_column
            + self.other_phones_columns
        )

    def _rename_df_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        renaming_dict = {column: f'RIESGO {index}' for index, column in enumerate(self.other_phones_columns, 1)}
        renaming_dict[self.main_phones_column[0]] = 'MASI'
        return df.rename(columns=renaming_dict)

    def _split_main_phones(self, df: pd.DataFrame) -> pd.DataFrame:

        splitted_main_phones = df['MASI'].str.split(self.main_phones_separator, expand=True)

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
                for ejec, data in self.results_dict.items():
                    csv_zip.writestr(
                        self.results_path / f"{ejec}.csv",
                        pd.DataFrame(data).to_csv(sep=';', encoding='ANSI', index=False),
                    )

        except Exception:
            print(traceback.format_exc())
