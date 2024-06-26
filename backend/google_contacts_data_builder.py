import base64
from pathlib import Path
import io
import zipfile

import pandas as pd


class GoogleContactsDataBuilder:

    def __init__(
        self,
        uploaded_datesheet_content: pd.DataFrame,
        identifier_column: list,
        full_name_column: list,
        main_phones_columns: list,
        other_phones_columns: list,
        column_to_group_by: list,
        main_phones_separator: str = '-',
    ) -> None:

        _, content_string = uploaded_datesheet_content.split(',')
        decoded = base64.b64decode(content_string)

        self.uploaded_datesheet = pd.read_csv(io.BytesIO(decoded), encoding='latin_1', sep=';', dtype=str)

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
        df_contacts = self._convert_phone_columns_into_row_values_with_phone_beside(df_contacts)

        df_contacts = self._create_google_contact_name_and_lastname_columns(df_contacts)

        # only to put columns in better order
        df_contacts = df_contacts.reindex(columns=['Nombre', 'Apellido', 'Trabajo', 'Ejecutivo'])

        for ejecutivo, datos in df_contacts.groupby(df_contacts[self.column_to_group_by[0]]):
            self.results_dict[ejecutivo] = datos[['Nombre', 'Apellido', 'Trabajo']].copy()

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

    def _convert_phone_columns_into_row_values_with_phone_beside(self, df: pd.DataFrame) -> pd.DataFrame:
        # to understand metl see: https://pandas.pydata.org/docs/user_guide/reshaping.html#reshaping-melt
        df = df.melt(id_vars=self.identifier_column + self.full_name_column + self.column_to_group_by)
        # delete rows with null values at any column
        df.dropna(axis='index', inplace=True)
        df = df.rename(columns={'variable': 'phone_type', 'value': 'Trabajo'})
        return df

    def _create_google_contact_name_and_lastname_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df["Nombre"] = df["phone_type"] + " " + df["Mat. Unica"]
        df.drop(['Mat. Unica', 'phone_type'], inplace=True, axis=1)
        df = df.rename(columns={'Razon Social': 'Apellido'})
        return df

    def get_results_as_zip_file(self) -> bytes:
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            for filename, df in self.results_dict.items():
                df_buffer = io.BytesIO()
                df.to_csv(df_buffer, index=False, sep=';')
                df_buffer.seek(0)
                zip_file.writestr(f'{filename}.csv', df_buffer.read())

        zip_buffer.seek(0)
        return zip_buffer.getvalue()
