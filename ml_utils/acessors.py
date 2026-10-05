# import base64
# import io
# import uuid
# import textwrap

# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd
# import seaborn as sns
# from IPython.display import clear_output, display, Markdown
# from ipywidgets import HTML, Button, HBox, Layout, VBox
# from matplotlib.patches import Circle


# @pd.api.extensions.register_dataframe_accessor("eda_utils")
# class CleanerAccessor:
#     def __init__(self, pandas_obj):
#         self._obj = pandas_obj

#     def convert_plot_to_html(self, fig):
#         """Конвертирует объект matplotlib figure в центрированную HTML-строку с собственным скроллом."""
#         buf = io.BytesIO()
#         fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
#         buf.seek(0)
#         img_base64 = base64.b64encode(buf.read()).decode('utf-8')
#         plt.close(fig)
#         return f"""
#         <div class="image-container">
#             <img src="data:image/png;base64,{img_base64}">
#         </div>
#         """

#     def create_page_layout(self, left_html, right_html):
#         """Разметка страницы 1/3 слева, 2/3 справа"""
#         return f"""
#         <div class="page">
#             <div class="left-container">
#                 {left_html}
#             </div>
#             <div class="right-container">
#                 {right_html}
#             </div>
#         </div>
#         """

#     def get_column_type(self, df, col):
#         """Автоматически определяет тип признака для выбора правильного анализа."""
#         dtype = df[col].dtype
#         nunique = df[col].nunique(dropna=True)

#         if pd.api.types.is_bool_dtype(dtype) or (pd.api.types.is_numeric_dtype(dtype) and nunique <= 2):
#             return 'boolean'
#         elif pd.api.types.is_datetime64_any_dtype(dtype):
#             return 'date'
#         elif pd.api.types.is_numeric_dtype(dtype):
#             return 'numeric'
#         else:
#             sample_idx = df[col].first_valid_index()
#             if sample_idx is not None:
#                 sample = df[col].loc[sample_idx]
#                 if isinstance(sample, str) and ('дат' in col.lower() or 'date' in col.lower() or 'time' in col.lower()):
#                     return 'date'
#             return 'categorical'

#     def safe_round(self, val, decimals=4):
#         """Безопасное округление (защита от NaN при вычислении асимметрии/эксцесса)."""
#         return round(val, decimals) if pd.notna(val) else "NaN"

#     def generate_overview_page(self, df):
#         """Создает первую страницу: Общая информация по всему датасету."""
#         types = df.dtypes.astype(str)
#         omissions_count = df.isna().sum()
#         omissions_share = round((df.isna().sum() / df.shape[0]) * 100, 2)
#         unique_count = df.nunique()
#         not_nan_count = df.notna().sum()

#         info_df = pd.DataFrame({
#             'Признак': df.columns,
#             'Тип': types.values,
#             'Кол-во (not-null)': not_nan_count.values,
#             'Пропуски': omissions_count.values,
#             'Доля пропусков (%)': omissions_share.values,
#             'Уникальных': unique_count.values
#         })

#         align_info = {'Признак': 'left', 'Тип': 'center',
#                       'Кол-во (not-null)': 'center', 'Пропуски': 'center', 'Доля пропусков (%)': 'center', 'Уникальных': 'center'}
#         info_headers = "".join(
#             [f"<th style='text-align: {align_info.get(col, 'center')} !important;'>{col}</th>" for col in info_df.columns])
#         info_rows = ""
#         for _, row in info_df.astype(str).iterrows():
#             info_rows += "<tr>" + \
#                 "".join(
#                     [f"<td style='text-align: {align_info.get(col, 'center')} !important;'>{row[col]}</td>" for col in info_df.columns]) + "</tr>"

#         styled_table = f"""
#         <div class="table-container">
#             <table><thead><tr>{info_headers}</tr></thead><tbody>{info_rows}</tbody></table>
#         </div>
#         """

#         dupes = df.duplicated().sum()
#         rows = df.shape[0]
#         cols = df.shape[1]

#         if isinstance(df.index, pd.RangeIndex):
#             idx_str = f"{df.index.start} по {df.index.stop - 1}"
#         else:
#             idx_str = f"Index: {len(df)} entries"

#         mem_bytes = df.memory_usage(deep=True).sum()
#         mem_kb = mem_bytes / 1024
#         mem_str = f"{mem_kb:.1f}+ KB" if mem_kb < 1024 else f"{mem_kb/1024:.2f}+ MB"

#         dtypes_df = df.dtypes.astype(str).value_counts().reset_index()
#         dtypes_df.columns = ['Тип данных', 'Количество']

#         align_dtypes = {'Тип данных': 'left', 'Количество': 'center'}
#         dtype_headers = "".join(
#             [f"<th style='text-align: {align_dtypes.get(col, 'center')} !important;'>{col}</th>" for col in dtypes_df.columns])
#         dtype_rows = ""
#         for _, row in dtypes_df.astype(str).iterrows():
#             dtype_rows += "<tr>" + \
#                 "".join(
#                     [f"<td style='text-align: {align_dtypes.get(col, 'center')} !important;'>{row[col]}</td>" for col in dtypes_df.columns]) + "</tr>"

#         dtype_html = f"""
#         <div class="table-container">
#             <table><thead><tr>{dtype_headers}</tr></thead><tbody>{dtype_rows}</tbody></table>
#         </div>
#         """

#         df_info = pd.DataFrame({
#             'Метрика': ['Количество строк', 'Индексы', 'Количество столбцов', 'Количество дубликатов', 'Используемая память'],
#             'Значение': [rows, f"с {idx_str}", cols, dupes, mem_str]
#         })

#         align_df_info = {'Метрика': 'left', 'Значение': 'center'}
#         df_info_headers = "".join(
#             [f"<th style='text-align: {align_df_info.get(col, 'center')} !important;'>{col}</th>" for col in df_info.columns])
#         df_info_rows = ""
#         for _, row in df_info.astype(str).iterrows():
#             df_info_rows += "<tr>" + \
#                 "".join(
#                     [f"<td style='text-align: {align_df_info.get(col, 'center')} !important;'>{row[col]}</td>" for col in df_info.columns]) + "</tr>"

#         df_info_table = f"""
#         <div class="table-container">
#             <table><thead><tr>{df_info_headers}</tr></thead><tbody>{df_info_rows}</tbody></table>
#         </div>
#         """

#         left_html = f"""
#         <div style="display: flex; flex-direction: column; gap: 10px; width: 100%; height: 100%; overflow-y: auto; box-sizing: border-box; font-family: sans-serif;">
#             <div style="display: flex; flex-direction: column;">
#                 <h3 class="table-title">Информация о датасете</h3>
#                 {df_info_table}
#             </div>
#             <div style="display: flex; flex-direction: column;">
#                 <h3 class="table-title">Количество столбцов по типам</h3>
#                 {dtype_html}
#             </div>
#         </div>
#         """

#         right_html = f"""
#         <div style="display: flex; flex-direction: column; width: 100%; height: 100%; box-sizing: border-box; font-family: sans-serif; padding-right: 5px;">
#             <h3 class="table-title">Информация о столбцах</h3>
#             {styled_table}
#         </div>
#         """

#         full_page_html = self.create_page_layout(left_html, right_html)
#         return {'title': 'Обзор датасета', 'content': full_page_html}

#     def generate_sample_page(self, df):
#         """Создает страницу со случайными строками для ознакомления с данными."""
#         sample_size = min(17, len(df))
#         sample_df = df.sample(sample_size, random_state=42)

#         align_sample = {}
#         sample_headers = "".join(
#             [f"<th style='text-align: {align_sample.get(col, 'left')} !important;'>{col}</th>" for col in sample_df.columns])
#         sample_rows = ""
#         for _, row in sample_df.astype(str).iterrows():
#             sample_rows += "<tr>" + \
#                 "".join(
#                     [f"<td style='text-align: {align_sample.get(col, 'left')} !important;'>{row[col]}</td>" for col in sample_df.columns]) + "</tr>"

#         styled_sample_table = f"""
#         <div class="table-container">
#             <table>
#                 <thead>
#                     <tr>{sample_headers}</tr>
#                 </thead>
#                 <tbody>{sample_rows}</tbody>
#             </table>
#         </div>
#         """

#         full_page_html = f"""
#         <div style="display: flex; flex-direction: column; width: 1160px; height: 480px; padding-right: 5px; overflow: auto;">
#             <h3 class="table-title">Случайные строки</h3>
#             {styled_sample_table}
#         </div>
#         """
#         return {'title': 'Случайные строки', 'content': full_page_html}

#     def generate_numeric_page(self, df, column):
#         """Анализ числового признака (Гистограмма + Ящик с усами)."""
#         series = df[column].dropna()
#         missing_count = df[column].isna().sum()
#         missing_percent = (missing_count / len(df)) * 100

#         stats_df = pd.DataFrame({
#             'Метрика': [
#                 'Название столбца',
#                 'Тип данных',
#                 'Количество строк',
#                 'Непустых',
#                 'Пропуски',
#                 'Среднее',
#                 'Медиана',
#                 'Стандартное отклонение',
#                 'Минимум',
#                 'Максимум',
#                 'Асимметрия',
#                 'Эксцесс'],
#             'Значение': [
#                 column,
#                 series.dtype,
#                 len(df),
#                 len(series),
#                 f"{missing_count} ({missing_percent:.2f}%)",
#                 self.safe_round(series.mean()),
#                 self.safe_round(series.median()),
#                 self.safe_round(series.std()),
#                 self.safe_round(series.min()),
#                 self.safe_round(series.max()),
#                 self.safe_round(series.skew() if len(series) > 2 else np.nan),
#                 self.safe_round(series.kurt() if len(series) > 3 else np.nan)
#             ]
#         })

#         align_stats = {'Метрика': 'left', 'Значение': 'center'}
#         stats_headers = "".join(
#             [f"<th style='text-align: {align_stats.get(col, 'center')} !important;'>{col}</th>" for col in stats_df.columns])
#         stats_rows = ""
#         for _, row in stats_df.astype(str).iterrows():
#             stats_rows += "<tr>" + \
#                 "".join(
#                     [f"<td style='text-align: {align_stats.get(col, 'center')} !important;'>{row[col]}</td>" for col in stats_df.columns]) + "</tr>"

#         table_html = f"""
#         <div style="display: flex; flex-direction: column;">
#             <h3 class="table-title">Общие сведения</h3>
#             <div class="table-container">
#                 <table>
#                     <thead>
#                         <tr>{stats_headers}</tr>
#                     </thead>
#                     <tbody>
#                         {stats_rows}
#                     </tbody>
#                 </table>
#             </div>
#         </div>
#         """

#         if series.empty:
#             plot_html = "<div style='text-align:center; width:100%;'><h3>Нет данных для построения графика</h3></div>"
#         else:
#             fig, axes = plt.subplots(
#                 nrows=2,
#                 ncols=1,
#                 figsize=(7.5, 4.5),
#                 gridspec_kw={"height_ratios": [0.8, 0.2]}
#             )

#             sns.histplot(
#                 series,
#                 bins=30,
#                 ax=axes[0],
#                 color="#2fa1a7",
#                 alpha=0.6,
#                 edgecolor="black",
#                 linewidth=0.5
#             )
#             axes[0].set_ylabel("Частота", fontsize=9)
#             axes[0].set_xlabel("")
#             axes[0].grid(color='gray', linestyle='-', alpha=0.3)
#             axes[0].set_axisbelow(False)

#             ax_kde = axes[0].twinx()

#             sns.kdeplot(
#                 series,
#                 ax=ax_kde,
#                 color="#eb3472",
#                 linewidth=1
#             )
#             ax_kde.set_ylabel("")
#             ax_kde.set_yticks([])

#             sns.boxplot(
#                 x=series,
#                 ax=axes[1],
#                 color="#2fa1a7",
#                 width=0.4,
#                 linewidth=1,
#                 linecolor="black",
#                 notch=True,
#                 fliersize=4,
#                 saturation=1,
#                 boxprops={'alpha': 0.6},
#                 flierprops={
#                     'marker': 'o',
#                     'markerfacecolor': '#eb3472',
#                     'markeredgecolor': 'none',
#                     'alpha': 0.4
#                 }
#             )
#             axes[1].set_xlabel("Значение", fontsize=9)
#             axes[1].grid(color='gray', linestyle='-', alpha=0.3)
#             axes[1].set_axisbelow(False)

#             plt.tight_layout()
#             plot_html = self.convert_plot_to_html(fig)

#         full_page_html = self.create_page_layout(table_html, plot_html)
#         return {'title': f"Столбец {column}", 'content': full_page_html}

#     def generate_categorical_page(self, df, column):
#         """Анализ категориального признака (Частотный анализ, редкие категории)."""
#         series = df[column].dropna()

#         missing_count = df[column].isna().sum()
#         missing_percent = (missing_count / len(df)) * 100
#         nunique = series.nunique()
#         counts = series.value_counts(normalize=True)
#         rare_cats_count = (counts < 0.01).sum()

#         stats_df = pd.DataFrame({
#             'Метрика': [
#                 'Название столбца',
#                 'Тип данных',
#                 'Количество строк',
#                 'Пропуски',
#                 'Уникальных значений',
#                 'Высокая кардинальность (>50)',
#                 'Редкие категории (<1%)'],
#             'Значение': [
#                 column,
#                 series.dtype,
#                 len(df),
#                 f"{missing_count} ({missing_percent:.2f}%)",
#                 nunique,
#                 "Да ⚠️" if nunique > 50 else "Нет",
#                 f"{rare_cats_count} шт."
#             ]
#         })

#         align_stats = {'Метрика': 'left', 'Значение': 'center'}
#         stats_headers = "".join(
#             [f"<th style='text-align: {align_stats.get(col, 'center')} !important;'>{col}</th>" for col in stats_df.columns])
#         stats_rows = ""
#         for _, row in stats_df.astype(str).iterrows():
#             stats_rows += "<tr>" + \
#                 "".join(
#                     [f"<td style='text-align: {align_stats.get(col, 'center')} !important;'>{row[col]}</td>" for col in stats_df.columns]) + "</tr>"

#         table_html = f"""
#         <div style="display: flex; flex-direction: column;">
#             <h3 class="table-title">Общие сведения</h3>
#             <div class="table-container">
#                 <table>
#                     <thead>
#                         <tr>{stats_headers}</tr>
#                     </thead>
#                     <tbody>
#                         {stats_rows}
#                     </tbody>
#                 </table>
#             </div>
#         </div>
#         """

#         if series.empty:
#             plot_html = "<div style='text-align:center; width:100%;'><h3>Нет данных</h3></div>"
#         else:
#             fig, ax = plt.subplots(figsize=(7.5, 4.5))
#             top_cats = series.value_counts().iloc[:15]

#             sns.barplot(
#                 y=top_cats.index.astype(str),
#                 x=top_cats.values,
#                 ax=ax,
#                 hue=top_cats.index,
#                 legend=False,
#                 alpha=0.6,
#                 edgecolor="black",
#                 linewidth=0.5,
#                 orient='h'
#             )

#             ax.set_title(f"Частотный анализ", fontsize=11, fontweight='bold')
#             ax.set_xlabel("Количество", fontsize=9)
#             ax.set_ylabel("")
#             ax.grid(color='gray', linestyle='-', alpha=0.3)

#             plt.tight_layout()
#             plot_html = self.convert_plot_to_html(fig)

#         full_page_html = self.create_page_layout(table_html, plot_html)
#         return {'title': f"Столбец {column}", 'content': full_page_html}

#     def generate_boolean_page(self, df, column):
#         """Анализ логического/бинарного признака (Дисбаланс классов)."""
#         series = df[column].dropna()

#         missing_count = df[column].isna().sum()
#         missing_percent = (missing_count / len(df)) * 100
#         counts = series.value_counts()

#         stats_list = [
#             ['Название столбца', column],
#             ['Тип данных', series.dtype],
#             ['Количество строк', len(df)],
#             ['Пропуски', f"{missing_count} ({missing_percent:.2f}%)"]
#         ]
#         for val, count in counts.items():
#             stats_list.append([f"Количество '{val}'", count])

#         stats_df = pd.DataFrame(stats_list, columns=['Метрика', 'Значение'])

#         align_stats = {'Метрика': 'left', 'Значение': 'center'}
#         stats_headers = "".join(
#             [f"<th style='text-align: {align_stats.get(col, 'center')} !important;'>{col}</th>" for col in stats_df.columns])
#         stats_rows = ""
#         for _, row in stats_df.astype(str).iterrows():
#             stats_rows += "<tr>" + \
#                 "".join(
#                     [f"<td style='text-align: {align_stats.get(col, 'center')} !important;'>{row[col]}</td>" for col in stats_df.columns]) + "</tr>"

#         table_html = f"""
#         <div style="display: flex; flex-direction: column;">
#             <h3 class="table-title">Общие сведения</h3>
#             <div class="table-container">
#                 <table>
#                     <thead>
#                         <tr>{stats_headers}</tr>
#                     </thead>
#                     <tbody>
#                         {stats_rows}
#                     </tbody>
#                 </table>
#             </div>
#         </div>
#         """

#         if series.empty:
#             plot_html = "<div style='text-align:center; width:100%;'><h3>Нет данных</h3></div>"
#         else:
#             fig, ax = plt.subplots(figsize=(7.5, 4.5))
#             colors = sns.color_palette('pastel')[0:len(counts)]

#             ax.pie(
#                 counts.values,
#                 labels=counts.index,
#                 autopct='%1.1f%%',
#                 startangle=90,
#                 colors=colors,
#                 wedgeprops={
#                     'edgecolor': 'white',
#                     'linewidth': 2
#                 }
#             )

#             centre_circle = Circle((0, 0), 0.65, fc='white')
#             fig.gca().add_artist(centre_circle)
#             ax.axis('equal')
#             ax.set_title(f"Баланс классов", fontsize=11, fontweight='bold')
#             plt.tight_layout()
#             plot_html = self.convert_plot_to_html(fig)

#         full_page_html = self.create_page_layout(table_html, plot_html)
#         return {'title': f"Столбец {column}", 'content': full_page_html}

#     def generate_date_page(self, df, column):
#         """Анализ дат (Временные дыры и равномерность)."""

#         empty_count = df[column].isna().sum()
#         dates = pd.to_datetime(df[column], errors='coerce')
#         total_nat = dates.isna().sum()
#         invalid_count = total_nat - empty_count
#         clean_dates = dates.dropna()

#         align_stats = {'Метрика': 'left', 'Значение': 'center'}

#         if clean_dates.empty:
#             err_df = pd.DataFrame({
#                 'Метрика': ['Ошибка'],
#                 'Значение': ['Нет дат']
#             })

#             err_headers = "".join(
#                 [f"<th style='text-align: {align_stats.get(col, 'center')} !important;'>{col}</th>" for col in err_df.columns])
#             err_rows = ""
#             for _, row in err_df.astype(str).iterrows():
#                 err_rows += "<tr>" + \
#                     "".join(
#                         [f"<td style='text-align: {align_stats.get(col, 'center')} !important;'>{row[col]}</td>" for col in err_df.columns]) + "</tr>"

#             table_html = f"""
#             <div style="display: flex; flex-direction: column;">
#                 <h3 class="table-title">Общие сведения</h3>
#                 <div class="table-container">
#                     <table>
#                         <thead>
#                             <tr>{err_headers}</tr>
#                         </thead>
#                         <tbody>{err_rows}</tbody>
#                     </table>
#                 </div>
#             </div>
#             """
#             plot_html = "<div style='text-align:center; width:100%;'><h3>Нет корректных дат</h3></div>"
#         else:
#             start_date = clean_dates.min()
#             end_date = clean_dates.max()
#             duration = end_date - start_date

#             stats_df = pd.DataFrame({
#                 'Метрика': [
#                     'Название столбца',
#                     'Тип данных',
#                     'Количество строк',
#                     'Пропуски',
#                     'Некорректный формат',
#                     'Начало периода',
#                     'Конец периода',
#                     'Продолжительность'
#                 ],
#                 'Значение': [
#                     column,
#                     df[column].dtype,
#                     len(df),
#                     empty_count,
#                     invalid_count,
#                     start_date.strftime('%Y-%m-%d'),
#                     end_date.strftime('%Y-%m-%d'),
#                     str(duration).split('.')[0]
#                 ]
#             })

#             stats_headers = "".join(
#                 [f"<th style='text-align: {align_stats.get(col, 'center')} !important;'>{col}</th>" for col in stats_df.columns])
#             stats_rows = ""
#             for _, row in stats_df.astype(str).iterrows():
#                 stats_rows += "<tr>" + \
#                     "".join(
#                         [f"<td style='text-align: {align_stats.get(col, 'center')} !important;'>{row[col]}</td>" for col in stats_df.columns]) + "</tr>"

#             table_html = f"""
#             <div style="display: flex; flex-direction: column;">
#                 <h3 class="table-title">Общие сведения</h3>
#                 <div class="table-container">
#                     <table>
#                         <thead>
#                             <tr>{stats_headers}</tr>
#                         </thead>
#                         <tbody>{stats_rows}</tbody>
#                     </table>
#                 </div>
#             </div>
#             """

#             fig, ax = plt.subplots(figsize=(7.5, 4.5))

#             sns.histplot(
#                 clean_dates,
#                 bins=30,
#                 ax=ax,
#                 color="#2fa1a7",
#                 alpha=0.6,
#                 edgecolor="black",
#                 linewidth=0.5
#             )

#             ax_kde = ax.twinx()

#             sns.kdeplot(
#                 clean_dates,
#                 ax=ax_kde,
#                 color="#eb3472",
#                 linewidth=1
#             )
#             ax_kde.set_ylabel("")
#             ax_kde.set_yticks([])

#             ax.set_title(f"Распределение во времени",
#                          fontsize=11, fontweight='bold')
#             ax.set_xlabel("Дата", fontsize=9)
#             ax.set_ylabel("Количество записей", fontsize=9)
#             ax.grid(True, color='gray', linestyle='-', alpha=0.3)

#             plt.xticks(rotation=30, ha='right')
#             plt.tight_layout()
#             plot_html = self.convert_plot_to_html(fig)

#         full_page_html = self.create_page_layout(table_html, plot_html)
#         return {'title': f"Столбец {column}", 'content': full_page_html}

#     def build_eda_dashboard(self, title="Комплексный EDA Анализ"):
#         """Генерирует все страницы и запускает интерактивный дашборд."""
#         print("⏳ Анализирую датасет и строю графики. Пожалуйста, подождите...")

#         pages = []

#         # Генерация страниц
#         pages.append(self.generate_overview_page(self._obj))
#         pages.append(self.generate_sample_page(self._obj))

#         for col in self._obj.columns:
#             col_type = self.get_column_type(self._obj, col)
#             if col_type == 'numeric':
#                 pages.append(self.generate_numeric_page(self._obj, col))
#             elif col_type == 'categorical':
#                 pages.append(self.generate_categorical_page(self._obj, col))
#             elif col_type == 'boolean':
#                 pages.append(self.generate_boolean_page(self._obj, col))
#             elif col_type == 'date':
#                 pages.append(self.generate_date_page(self._obj, col))

#         current_page_idx = [0]
#         total_pages = len(pages)

#         # Элементы интерфейса
#         header_widget = HTML(layout=Layout(flex='1'))
#         content_widget = HTML(layout=Layout(
#             width='100%', height='auto', display='flex', justify_content='center'))

#         btn_prev = Button(description="◀", layout=Layout(
#             width='36px', height='36px'))
#         btn_next = Button(description="▶", layout=Layout(
#             width='36px', height='36px'))

#         def update_state():
#             idx = current_page_idx[0]
#             page = pages[idx]

#             header_widget.value = f"""
#             <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
#                 <h2 style="font-weight: bold;">{title}: {page['title']}</h2>
#                 <h4 style="margin: 0; margin-right: 10px;">Страница {idx + 1} из {total_pages}</h4>
#             </div>
#             """
#             content_widget.value = page['content']

#             btn_prev.disabled = (idx == 0)
#             btn_next.disabled = (idx == total_pages - 1)

#         def on_prev(b):
#             if current_page_idx[0] > 0:
#                 current_page_idx[0] -= 1
#                 update_state()

#         def on_next(b):
#             if current_page_idx[0] < total_pages - 1:
#                 current_page_idx[0] += 1
#                 update_state()

#         btn_prev.on_click(on_prev)
#         btn_next.on_click(on_next)

#         update_state()

#         top_panel = HBox([header_widget, btn_prev, btn_next], layout=Layout(display='flex', justify_content='space-between',
#                          align_items='center', padding='5px 10px', border_bottom='1px solid #ddd', margin='0px 0px 15px 0px', width='100%'))

#         global_styles = HTML(value="""
#         <style>
#             .dashboard-wrapper {
#                 background-color: #ffffff !important; 
#             }

#             .image-container {
#                 width: 100%; 
#                 max-height: 480px; 
#                 overflow: auto; 
#                 text-align: center;    
#             }
                                    
#             .image-container img {
#                 max-width: 100%; 
#                 height: auto; 
#                 display: block; 
#                 margin: 0 auto;                        
#             }
                                    
#             .page {
#                 display: flex; 
#                 width: 100%; 
#                 height: 480px; 
#                 gap: 10px; 
#                 align-items: flex-start; 
#                 justify-content: center;   
#                 box-sizing: border-box;   
#             }
                                    
#             .left-container {
#                 width: 33%; 
#                 height: 100%; 
#                 display: flex; 
#                 flex-direction: column; 
#                 overflow: hidden;
#                 box-sizing: border-box;
#             }
                                    
#             .right-container {
#                 width: 67%; 
#                 height: 100%; 
#                 display: flex; 
#                 flex-direction: column; 
#                 overflow: hidden;       
#                 box-sizing: border-box;    
#             }
                                    
#             .table-title {
#                 margin: 0;
#             }
                                    
#             .table-container {
#                 width: 100%; 
#                 max-height: 480px; 
#                 overflow: auto;
#                 font-family: sans-serif; 
#                 border: 1px solid #ddd; 
#                 border-radius: 6px;
#                 box-sizing: border-box;                   
#             }
                                    
#             .table-container table { 
#                 width: 100%; 
#                 border-collapse: separate; 
#                 border-spacing: 0; 
#                 margin: 0; 
#                 white-space: nowrap;
#             }
                
#             .table-container th { 
#                 background-color: #f2f2f2 !important; 
#                 padding: 4px 8px; 
#                 border-bottom: 1px solid #ddd; 
#                 font-size: 12px; 
#                 line-height: 1.2; 
#                 position: sticky; 
#                 top: 0; 
#                 z-index: 1; 
#             }
                
#             .table-container td { 
#                 background-color: #ffffff !important; 
#                 padding: 4px 8px; 
#                 border-bottom: 1px solid #eee; 
#                 font-size: 12px; 
#                 line-height: 1.2; 
#             }
            
#             .table-container tr:last-child td { 
#                 border-bottom: none; 
#             }
#         </style>
#         """)

#         dashboard_layout = VBox(
#             [
#                 global_styles,
#                 top_panel,
#                 content_widget
#             ],
#             layout=Layout(
#                 display='flex',
#                 flex_direction='column',
#                 width='100%',
#                 height='auto',
#                 overflow='hidden'
#             )
#         )
#         dashboard_layout.add_class('dashboard-wrapper')

#         clear_output()
#         display(dashboard_layout)


import base64
import io
import uuid
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from IPython.display import clear_output, display, Markdown
from ipywidgets import HTML, Button, HBox, Layout, VBox
from matplotlib.patches import Circle


@pd.api.extensions.register_dataframe_accessor("eda_utils")
class CleanerAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def convert_plot_to_html(self, fig):
        """Конвертирует объект matplotlib figure в центрированную HTML-строку с собственным скроллом."""
        buf = io.BytesIO()
        # Добавлен facecolor='white', чтобы графики гарантированно сохраняли белый фон
        fig.savefig(buf, format='png', bbox_inches='tight',
                    dpi=100, facecolor='white')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return f"""
        <div class="image-container">
            <img src="data:image/png;base64,{img_base64}">
        </div>
        """

    def create_page_layout(self, left_html, right_html):
        """Разметка страницы 1/3 слева, 2/3 справа"""
        return f"""
        <div class="page">
            <div class="left-container">
                {left_html}
            </div>
            <div class="right-container">
                {right_html}
            </div>
        </div>
        """

    def get_column_type(self, df, col):
        """Автоматически определяет тип признака для выбора правильного анализа."""
        dtype = df[col].dtype
        nunique = df[col].nunique(dropna=True)

        if pd.api.types.is_bool_dtype(dtype) or (pd.api.types.is_numeric_dtype(dtype) and nunique <= 2):
            return 'boolean'
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return 'date'
        elif pd.api.types.is_numeric_dtype(dtype):
            return 'numeric'
        else:
            sample_idx = df[col].first_valid_index()
            if sample_idx is not None:
                sample = df[col].loc[sample_idx]
                if isinstance(sample, str) and ('дат' in col.lower() or 'date' in col.lower() or 'time' in col.lower()):
                    return 'date'
            return 'categorical'

    def safe_round(self, val, decimals=4):
        """Безопасное округление (защита от NaN при вычислении асимметрии/эксцесса)."""
        return round(val, decimals) if pd.notna(val) else "NaN"

    def generate_overview_page(self, df):
        """Создает первую страницу: Общая информация по всему датасету."""
        types = df.dtypes.astype(str)
        omissions_count = df.isna().sum()
        omissions_share = round((df.isna().sum() / df.shape[0]) * 100, 2)
        unique_count = df.nunique()
        not_nan_count = df.notna().sum()

        info_df = pd.DataFrame({
            'Признак': df.columns,
            'Тип': types.values,
            'Кол-во (not-null)': not_nan_count.values,
            'Пропуски': omissions_count.values,
            'Доля пропусков (%)': omissions_share.values,
            'Уникальных': unique_count.values
        })

        align_info = {'Признак': 'left', 'Тип': 'center',
                      'Кол-во (not-null)': 'center', 'Пропуски': 'center', 'Доля пропусков (%)': 'center', 'Уникальных': 'center'}
        info_headers = "".join(
            [f"<th style='text-align: {align_info.get(col, 'center')} !important;'>{col}</th>" for col in info_df.columns])
        info_rows = ""
        for _, row in info_df.astype(str).iterrows():
            info_rows += "<tr>" + \
                "".join(
                    [f"<td style='text-align: {align_info.get(col, 'center')} !important;'>{row[col]}</td>" for col in info_df.columns]) + "</tr>"

        styled_table = f"""
        <div class="table-container">
            <table><thead><tr>{info_headers}</tr></thead><tbody>{info_rows}</tbody></table>
        </div>
        """

        dupes = df.duplicated().sum()
        rows = df.shape[0]
        cols = df.shape[1]

        if isinstance(df.index, pd.RangeIndex):
            idx_str = f"{df.index.start} по {df.index.stop - 1}"
        else:
            idx_str = f"Index: {len(df)} entries"

        mem_bytes = df.memory_usage(deep=True).sum()
        mem_kb = mem_bytes / 1024
        mem_str = f"{mem_kb:.1f}+ KB" if mem_kb < 1024 else f"{mem_kb/1024:.2f}+ MB"

        dtypes_df = df.dtypes.astype(str).value_counts().reset_index()
        dtypes_df.columns = ['Тип данных', 'Количество']

        align_dtypes = {'Тип данных': 'left', 'Количество': 'center'}
        dtype_headers = "".join(
            [f"<th style='text-align: {align_dtypes.get(col, 'center')} !important;'>{col}</th>" for col in dtypes_df.columns])
        dtype_rows = ""
        for _, row in dtypes_df.astype(str).iterrows():
            dtype_rows += "<tr>" + \
                "".join(
                    [f"<td style='text-align: {align_dtypes.get(col, 'center')} !important;'>{row[col]}</td>" for col in dtypes_df.columns]) + "</tr>"

        dtype_html = f"""
        <div class="table-container">
            <table><thead><tr>{dtype_headers}</tr></thead><tbody>{dtype_rows}</tbody></table>
        </div>
        """

        df_info = pd.DataFrame({
            'Метрика': ['Количество строк', 'Индексы', 'Количество столбцов', 'Количество дубликатов', 'Используемая память'],
            'Значение': [rows, f"с {idx_str}", cols, dupes, mem_str]
        })

        align_df_info = {'Метрика': 'left', 'Значение': 'center'}
        df_info_headers = "".join(
            [f"<th style='text-align: {align_df_info.get(col, 'center')} !important;'>{col}</th>" for col in df_info.columns])
        df_info_rows = ""
        for _, row in df_info.astype(str).iterrows():
            df_info_rows += "<tr>" + \
                "".join(
                    [f"<td style='text-align: {align_df_info.get(col, 'center')} !important;'>{row[col]}</td>" for col in df_info.columns]) + "</tr>"

        df_info_table = f"""
        <div class="table-container">
            <table><thead><tr>{df_info_headers}</tr></thead><tbody>{df_info_rows}</tbody></table>
        </div>
        """

        left_html = f"""
        <div style="display: flex; flex-direction: column; gap: 10px; width: 100%; height: 100%; overflow-y: auto; box-sizing: border-box; font-family: sans-serif;">
            <div style="display: flex; flex-direction: column;">
                <h3 class="table-title">Информация о датасете</h3>
                {df_info_table}
            </div>
            <div style="display: flex; flex-direction: column;">
                <h3 class="table-title">Количество столбцов по типам</h3>
                {dtype_html}
            </div>
        </div>
        """

        right_html = f"""
        <div style="display: flex; flex-direction: column; width: 100%; height: 100%; box-sizing: border-box; font-family: sans-serif; padding-right: 5px;">
            <h3 class="table-title">Информация о столбцах</h3>
            {styled_table}
        </div>
        """

        full_page_html = self.create_page_layout(left_html, right_html)
        return {'title': 'Обзор датасета', 'content': full_page_html}

    def generate_sample_page(self, df):
        """Создает страницу со случайными строками для ознакомления с данными."""
        sample_size = min(17, len(df))
        sample_df = df.sample(sample_size, random_state=42)

        align_sample = {}
        sample_headers = "".join(
            [f"<th style='text-align: {align_sample.get(col, 'left')} !important;'>{col}</th>" for col in sample_df.columns])
        sample_rows = ""
        for _, row in sample_df.astype(str).iterrows():
            sample_rows += "<tr>" + \
                "".join(
                    [f"<td style='text-align: {align_sample.get(col, 'left')} !important;'>{row[col]}</td>" for col in sample_df.columns]) + "</tr>"

        styled_sample_table = f"""
        <div class="table-container">
            <table>
                <thead>
                    <tr>{sample_headers}</tr>
                </thead>
                <tbody>{sample_rows}</tbody>
            </table>
        </div>
        """

        full_page_html = f"""
        <div style="display: flex; flex-direction: column; width: 1160px; height: 480px; padding-right: 5px; overflow: auto;">
            <h3 class="table-title">Случайные строки</h3>
            {styled_sample_table}
        </div>
        """
        return {'title': 'Случайные строки', 'content': full_page_html}

    def generate_numeric_page(self, df, column):
        """Анализ числового признака (Гистограмма + Ящик с усами)."""
        series = df[column].dropna()
        missing_count = df[column].isna().sum()
        missing_percent = (missing_count / len(df)) * 100

        stats_df = pd.DataFrame({
            'Метрика': [
                'Название столбца',
                'Тип данных',
                'Количество строк',
                'Непустых',
                'Пропуски',
                'Среднее',
                'Медиана',
                'Стандартное отклонение',
                'Минимум',
                'Максимум',
                'Асимметрия',
                'Эксцесс'],
            'Значение': [
                column,
                series.dtype,
                len(df),
                len(series),
                f"{missing_count} ({missing_percent:.2f}%)",
                self.safe_round(series.mean()),
                self.safe_round(series.median()),
                self.safe_round(series.std()),
                self.safe_round(series.min()),
                self.safe_round(series.max()),
                self.safe_round(series.skew() if len(series) > 2 else np.nan),
                self.safe_round(series.kurt() if len(series) > 3 else np.nan)
            ]
        })

        align_stats = {'Метрика': 'left', 'Значение': 'center'}
        stats_headers = "".join(
            [f"<th style='text-align: {align_stats.get(col, 'center')} !important;'>{col}</th>" for col in stats_df.columns])
        stats_rows = ""
        for _, row in stats_df.astype(str).iterrows():
            stats_rows += "<tr>" + \
                "".join(
                    [f"<td style='text-align: {align_stats.get(col, 'center')} !important;'>{row[col]}</td>" for col in stats_df.columns]) + "</tr>"

        table_html = f"""
        <div style="display: flex; flex-direction: column;">
            <h3 class="table-title">Общие сведения</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>{stats_headers}</tr>
                    </thead>
                    <tbody>
                        {stats_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

        if series.empty:
            plot_html = "<div style='text-align:center; width:100%;'><h3>Нет данных для построения графика</h3></div>"
        else:
            with plt.style.context('default'):
                fig, axes = plt.subplots(
                    nrows=2,
                    ncols=1,
                    figsize=(7.5, 4.5),
                    gridspec_kw={"height_ratios": [0.8, 0.2]}
                )

                sns.histplot(
                    series,
                    bins=30,
                    ax=axes[0],
                    color="#2fa1a7",
                    alpha=0.6,
                    edgecolor="black",
                    linewidth=0.5
                )
                axes[0].set_ylabel("Частота", fontsize=9)
                axes[0].set_xlabel("")
                axes[0].grid(color='gray', linestyle='-', alpha=0.3)
                axes[0].set_axisbelow(False)

                ax_kde = axes[0].twinx()

                sns.kdeplot(
                    series,
                    ax=ax_kde,
                    color="#eb3472",
                    linewidth=1
                )
                ax_kde.set_ylabel("")
                ax_kde.set_yticks([])

                sns.boxplot(
                    x=series,
                    ax=axes[1],
                    color="#2fa1a7",
                    width=0.4,
                    linewidth=1,
                    linecolor="black",
                    notch=True,
                    fliersize=4,
                    saturation=1,
                    boxprops={'alpha': 0.6},
                    flierprops={
                        'marker': 'o',
                        'markerfacecolor': '#eb3472',
                        'markeredgecolor': 'none',
                        'alpha': 0.4
                    }
                )
                axes[1].set_xlabel("Значение", fontsize=9)
                axes[1].grid(color='gray', linestyle='-', alpha=0.3)
                axes[1].set_axisbelow(False)

                plt.tight_layout()
                plot_html = self.convert_plot_to_html(fig)

        full_page_html = self.create_page_layout(table_html, plot_html)
        return {'title': f"Столбец {column}", 'content': full_page_html}

    def generate_categorical_page(self, df, column):
        """Анализ категориального признака (Частотный анализ, редкие категории)."""
        series = df[column].dropna()

        missing_count = df[column].isna().sum()
        missing_percent = (missing_count / len(df)) * 100
        nunique = series.nunique()
        counts = series.value_counts(normalize=True)
        rare_cats_count = (counts < 0.01).sum()

        stats_df = pd.DataFrame({
            'Метрика': [
                'Название столбца',
                'Тип данных',
                'Количество строк',
                'Пропуски',
                'Уникальных значений',
                'Высокая кардинальность (>50)',
                'Редкие категории (<1%)'],
            'Значение': [
                column,
                series.dtype,
                len(df),
                f"{missing_count} ({missing_percent:.2f}%)",
                nunique,
                "Да ⚠️" if nunique > 50 else "Нет",
                f"{rare_cats_count} шт."
            ]
        })

        align_stats = {'Метрика': 'left', 'Значение': 'center'}
        stats_headers = "".join(
            [f"<th style='text-align: {align_stats.get(col, 'center')} !important;'>{col}</th>" for col in stats_df.columns])
        stats_rows = ""
        for _, row in stats_df.astype(str).iterrows():
            stats_rows += "<tr>" + \
                "".join(
                    [f"<td style='text-align: {align_stats.get(col, 'center')} !important;'>{row[col]}</td>" for col in stats_df.columns]) + "</tr>"

        table_html = f"""
        <div style="display: flex; flex-direction: column;">
            <h3 class="table-title">Общие сведения</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>{stats_headers}</tr>
                    </thead>
                    <tbody>
                        {stats_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

        if series.empty:
            plot_html = "<div style='text-align:center; width:100%;'><h3>Нет данных</h3></div>"
        else:
            with plt.style.context('default'):
                fig, ax = plt.subplots(figsize=(7.5, 4.5))
                top_cats = series.value_counts().iloc[:15]

                sns.barplot(
                    y=top_cats.index.astype(str),
                    x=top_cats.values,
                    ax=ax,
                    hue=top_cats.index,
                    legend=False,
                    alpha=0.6,
                    edgecolor="black",
                    linewidth=0.5,
                    orient='h'
                )

                ax.set_title(f"Частотный анализ",
                             fontsize=11, fontweight='bold')
                ax.set_xlabel("Количество", fontsize=9)
                ax.set_ylabel("")
                ax.grid(color='gray', linestyle='-', alpha=0.3)

                plt.tight_layout()
                plot_html = self.convert_plot_to_html(fig)

        full_page_html = self.create_page_layout(table_html, plot_html)
        return {'title': f"Столбец {column}", 'content': full_page_html}

    def generate_boolean_page(self, df, column):
        """Анализ логического/бинарного признака (Дисбаланс классов)."""
        series = df[column].dropna()

        missing_count = df[column].isna().sum()
        missing_percent = (missing_count / len(df)) * 100
        counts = series.value_counts()

        stats_list = [
            ['Название столбца', column],
            ['Тип данных', series.dtype],
            ['Количество строк', len(df)],
            ['Пропуски', f"{missing_count} ({missing_percent:.2f}%)"]
        ]
        for val, count in counts.items():
            stats_list.append([f"Количество '{val}'", count])

        stats_df = pd.DataFrame(stats_list, columns=['Метрика', 'Значение'])

        align_stats = {'Метрика': 'left', 'Значение': 'center'}
        stats_headers = "".join(
            [f"<th style='text-align: {align_stats.get(col, 'center')} !important;'>{col}</th>" for col in stats_df.columns])
        stats_rows = ""
        for _, row in stats_df.astype(str).iterrows():
            stats_rows += "<tr>" + \
                "".join(
                    [f"<td style='text-align: {align_stats.get(col, 'center')} !important;'>{row[col]}</td>" for col in stats_df.columns]) + "</tr>"

        table_html = f"""
        <div style="display: flex; flex-direction: column;">
            <h3 class="table-title">Общие сведения</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>{stats_headers}</tr>
                    </thead>
                    <tbody>
                        {stats_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

        if series.empty:
            plot_html = "<div style='text-align:center; width:100%;'><h3>Нет данных</h3></div>"
        else:
            with plt.style.context('default'):
                fig, ax = plt.subplots(figsize=(7.5, 4.5))
                colors = sns.color_palette('pastel')[0:len(counts)]

                ax.pie(
                    counts.values,
                    labels=counts.index,
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=colors,
                    wedgeprops={
                        'edgecolor': 'white',
                        'linewidth': 2
                    }
                )

                centre_circle = Circle((0, 0), 0.65, fc='white')
                fig.gca().add_artist(centre_circle)
                ax.axis('equal')
                ax.set_title(f"Баланс классов", fontsize=11, fontweight='bold')
                plt.tight_layout()
                plot_html = self.convert_plot_to_html(fig)

        full_page_html = self.create_page_layout(table_html, plot_html)
        return {'title': f"Столбец {column}", 'content': full_page_html}

    def generate_date_page(self, df, column):
        """Анализ дат (Временные дыры и равномерность)."""

        empty_count = df[column].isna().sum()
        dates = pd.to_datetime(df[column], errors='coerce')
        total_nat = dates.isna().sum()
        invalid_count = total_nat - empty_count
        clean_dates = dates.dropna()

        align_stats = {'Метрика': 'left', 'Значение': 'center'}

        if clean_dates.empty:
            err_df = pd.DataFrame({
                'Метрика': ['Ошибка'],
                'Значение': ['Нет дат']
            })

            err_headers = "".join(
                [f"<th style='text-align: {align_stats.get(col, 'center')} !important;'>{col}</th>" for col in err_df.columns])
            err_rows = ""
            for _, row in err_df.astype(str).iterrows():
                err_rows += "<tr>" + \
                    "".join(
                        [f"<td style='text-align: {align_stats.get(col, 'center')} !important;'>{row[col]}</td>" for col in err_df.columns]) + "</tr>"

            table_html = f"""
            <div style="display: flex; flex-direction: column;">
                <h3 class="table-title">Общие сведения</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>{err_headers}</tr>
                        </thead>
                        <tbody>{err_rows}</tbody>
                    </table>
                </div>
            </div>
            """
            plot_html = "<div style='text-align:center; width:100%;'><h3>Нет корректных дат</h3></div>"
        else:
            start_date = clean_dates.min()
            end_date = clean_dates.max()
            duration = end_date - start_date

            stats_df = pd.DataFrame({
                'Метрика': [
                    'Название столбца',
                    'Тип данных',
                    'Количество строк',
                    'Пропуски',
                    'Некорректный формат',
                    'Начало периода',
                    'Конец периода',
                    'Продолжительность'
                ],
                'Значение': [
                    column,
                    df[column].dtype,
                    len(df),
                    empty_count,
                    invalid_count,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d'),
                    str(duration).split('.')[0]
                ]
            })

            stats_headers = "".join(
                [f"<th style='text-align: {align_stats.get(col, 'center')} !important;'>{col}</th>" for col in stats_df.columns])
            stats_rows = ""
            for _, row in stats_df.astype(str).iterrows():
                stats_rows += "<tr>" + \
                    "".join(
                        [f"<td style='text-align: {align_stats.get(col, 'center')} !important;'>{row[col]}</td>" for col in stats_df.columns]) + "</tr>"

            table_html = f"""
            <div style="display: flex; flex-direction: column;">
                <h3 class="table-title">Общие сведения</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>{stats_headers}</tr>
                        </thead>
                        <tbody>{stats_rows}</tbody>
                    </table>
                </div>
            </div>
            """

            with plt.style.context('default'):
                fig, ax = plt.subplots(figsize=(7.5, 4.5))

                sns.histplot(
                    clean_dates,
                    bins=30,
                    ax=ax,
                    color="#2fa1a7",
                    alpha=0.6,
                    edgecolor="black",
                    linewidth=0.5
                )

                ax_kde = ax.twinx()

                sns.kdeplot(
                    clean_dates,
                    ax=ax_kde,
                    color="#eb3472",
                    linewidth=1
                )
                ax_kde.set_ylabel("")
                ax_kde.set_yticks([])

                ax.set_title(f"Распределение во времени",
                             fontsize=11, fontweight='bold')
                ax.set_xlabel("Дата", fontsize=9)
                ax.set_ylabel("Количество записей", fontsize=9)
                ax.grid(True, color='gray', linestyle='-', alpha=0.3)

                plt.xticks(rotation=30, ha='right')
                plt.tight_layout()
                plot_html = self.convert_plot_to_html(fig)

        full_page_html = self.create_page_layout(table_html, plot_html)
        return {'title': f"Столбец {column}", 'content': full_page_html}

    def build_eda_dashboard(self, title="Комплексный EDA Анализ"):
        """Генерирует все страницы и запускает интерактивный дашборд."""
        print("⏳ Анализирую датасет и строю графики. Пожалуйста, подождите...")

        pages = []

        # Генерация страниц
        pages.append(self.generate_overview_page(self._obj))
        pages.append(self.generate_sample_page(self._obj))

        for col in self._obj.columns:
            col_type = self.get_column_type(self._obj, col)
            if col_type == 'numeric':
                pages.append(self.generate_numeric_page(self._obj, col))
            elif col_type == 'categorical':
                pages.append(self.generate_categorical_page(self._obj, col))
            elif col_type == 'boolean':
                pages.append(self.generate_boolean_page(self._obj, col))
            elif col_type == 'date':
                pages.append(self.generate_date_page(self._obj, col))

        current_page_idx = [0]
        total_pages = len(pages)

        # Элементы интерфейса
        header_widget = HTML(layout=Layout(flex='1'))
        content_widget = HTML(layout=Layout(
            width='100%', height='auto', display='flex', justify_content='center'))

        btn_prev = Button(description="◀", layout=Layout(
            width='36px', height='36px'))
        btn_next = Button(description="▶", layout=Layout(
            width='36px', height='36px'))

        # Жестко прописываем стиль кнопок в обход темы Jupyter/Colab
        btn_prev.style.button_color = '#f2f2f2'
        btn_prev.style.text_color = '#212121'
        btn_next.style.button_color = '#f2f2f2'
        btn_next.style.text_color = '#212121'

        def update_state():
            idx = current_page_idx[0]
            page = pages[idx]

            # Оборачиваем header в жесткий inline-сброс
            header_widget.value = f"""
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; color: #212121 !important; background-color: transparent;">
                <h2 style="font-weight: bold; margin: 0; color: #212121 !important;">{title}: {page['title']}</h2>
                <h4 style="margin: 0; margin-right: 10px; color: #212121 !important;">Страница {idx + 1} из {total_pages}</h4>
            </div>
            """
            content_widget.value = page['content']

            btn_prev.disabled = (idx == 0)
            btn_next.disabled = (idx == total_pages - 1)

        def on_prev(b):
            if current_page_idx[0] > 0:
                current_page_idx[0] -= 1
                update_state()

        def on_next(b):
            if current_page_idx[0] < total_pages - 1:
                current_page_idx[0] += 1
                update_state()

        btn_prev.on_click(on_prev)
        btn_next.on_click(on_next)

        update_state()

        top_panel = HBox([header_widget, btn_prev, btn_next], layout=Layout(display='flex', justify_content='space-between',
                         align_items='center', padding='5px 10px', border_bottom='1px solid #ddd', margin='0px 0px 15px 0px', width='100%'))

        # Экстремально специфичный CSS со сбросом глобальных переменных
        global_styles = HTML(value="""
        <style>
            /* 1. Нейтрализуем инъекции переменных из Colab и Jupyter для нашего виджета */
            .dashboard-wrapper {
                --colab-primary-text-color: #212121 !important;
                --colab-bg-color: #ffffff !important;
                --colab-border-color: #dddddd !important;
                --colab-callout-background-color: #f2f2f2 !important;
                --jp-ui-font-color1: #212121 !important;
                --jp-layout-color1: #ffffff !important;
                
                background-color: #ffffff !important;
                color: #212121 !important;
            }

            /* 2. Принудительно окрашиваем весь текст внутри виджета (включая span и div от Colab) */
            .dashboard-wrapper * {
                color: #212121 !important;
            }

            .dashboard-wrapper .image-container {
                width: 100%; 
                max-height: 480px; 
                overflow: auto; 
                text-align: center;
                background-color: #ffffff !important;    
            }
                                    
            .dashboard-wrapper .image-container img {
                max-width: 100%; 
                height: auto; 
                display: block; 
                margin: 0 auto;                        
            }
                                    
            .dashboard-wrapper .page {
                display: flex; 
                width: 100%; 
                height: 480px; 
                gap: 10px; 
                align-items: flex-start; 
                justify-content: center;   
                box-sizing: border-box; 
                background-color: #ffffff !important;  
            }
                                    
            .dashboard-wrapper .left-container {
                width: 33%; 
                height: 100%; 
                display: flex; 
                flex-direction: column; 
                overflow: hidden;
                box-sizing: border-box;
                background-color: #ffffff !important;
            }
                                    
            .dashboard-wrapper .right-container {
                width: 67%; 
                height: 100%; 
                display: flex; 
                flex-direction: column; 
                overflow: hidden;       
                box-sizing: border-box; 
                background-color: #ffffff !important;   
            }
                                    
            .dashboard-wrapper .table-title {
                margin: 0 0 5px 0 !important;
                color: #212121 !important;
            }
                                    
            .dashboard-wrapper .table-container {
                width: 100%; 
                max-height: 480px; 
                overflow: auto;
                font-family: sans-serif; 
                border: 1px solid #ddd !important; 
                border-radius: 6px;
                box-sizing: border-box; 
                background-color: #ffffff !important;                  
            }
                                    
            .dashboard-wrapper .table-container table { 
                width: 100%; 
                border-collapse: separate; 
                border-spacing: 0; 
                margin: 0; 
                white-space: nowrap;
                background-color: #ffffff !important;
            }
            
            /* 3. Усиленные селекторы ячеек, которые не пробить глобальным CSS (html body ...) */
            html body .dashboard-wrapper th,
            .dashboard-wrapper th,
            .dashboard-wrapper .table-container th { 
                background-color: #f2f2f2 !important; 
                color: #212121 !important; 
                padding: 4px 8px !important; 
                border-bottom: 1px solid #ddd !important;
                border-top: none !important;
                border-left: none !important;
                border-right: none !important; 
                font-size: 12px !important; 
                line-height: 1.2 !important; 
                position: sticky !important; 
                top: 0 !important; 
                z-index: 1 !important; 
            }
            
            html body .dashboard-wrapper td,    
            .dashboard-wrapper td,
            .dashboard-wrapper .table-container td { 
                background-color: #ffffff !important; 
                color: #212121 !important; 
                padding: 4px 8px !important; 
                border-bottom: 1px solid #eee !important;
                border-top: none !important;
                border-left: none !important;
                border-right: none !important; 
                font-size: 12px !important; 
                line-height: 1.2 !important; 
            }
            
            .dashboard-wrapper .table-container tr:last-child td { 
                border-bottom: none !important; 
            }
        </style>
        """)

        dashboard_layout = VBox(
            [
                global_styles,
                top_panel,
                content_widget
            ],
            layout=Layout(
                display='flex',
                flex_direction='column',
                width='100%',
                height='auto',
                overflow='hidden'
            )
        )
        dashboard_layout.add_class('dashboard-wrapper')

        clear_output()
        display(dashboard_layout)




# import base64
# import io
# import numpy as np
# import pandas as pd
# import seaborn as sns
# import matplotlib.pyplot as plt
# from IPython.display import clear_output, display, Markdown
# from matplotlib.patches import Circle


# @pd.api.extensions.register_dataframe_accessor("eda_utils")
# class CleanerAccessor:
#     def __init__(self, pandas_obj):
#         self._obj = pandas_obj

#     def convert_plot_to_md(self, fig, alt_text="График"):
#         """Конвертирует объект matplotlib figure в Markdown-изображение Base64."""
#         buf = io.BytesIO()
#         fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
#         buf.seek(0)
#         img_base64 = base64.b64encode(buf.read()).decode('utf-8')
#         plt.close(fig)
#         return f"![{alt_text}](data:image/png;base64,{img_base64})"

#     def _draw_table(self, ax, df, title):
#         """Отрисовывает DataFrame как красивую таблицу прямо на холсте matplotlib с фиксированной высотой строк."""
#         ax.axis('off')

#         # Выравниваем заголовок по левому краю, прямо над таблицей
#         ax.set_title(title, fontsize=12, fontweight='bold', loc='left', pad=15)

#         # ДИНАМИЧЕСКИЙ РАСЧЕТ ВЫСОТЫ:
#         # Каждая строка занимает ровно 6.5% высоты блока (~30-35px).
#         num_rows = len(df) + 1  # Строки данных + 1 строка заголовка
#         row_height = 0.065
#         table_height = num_rows * row_height

#         # Прижимаем таблицу к самому верху (y=1.0) и откладываем высоту вниз
#         bbox = [0, 1.0 - table_height, 1, table_height]

#         table = ax.table(cellText=df.values, colLabels=df.columns,
#                          loc='top', cellLoc='left', bbox=bbox)
#         table.auto_set_font_size(False)
#         table.set_fontsize(10)

#         # Стилизация ячеек
#         for (row, col), cell in table.get_celld().items():
#             if row == 0:
#                 cell.set_text_props(weight='bold')
#                 cell.set_facecolor('#f0f0f0')  # Светло-серый фон для заголовка

#             cell.set_edgecolor('#d3d3d3')

#             # Левая колонка (названия метрик) - 60% ширины, Правая (значения) - 40%.
#             # Теперь любой длинный текст точно поместится.
#             if col == 0:
#                 cell.set_width(0.60)
#             elif col == 1:
#                 cell.set_width(0.40)

#     def get_column_type(self, df, col):
#         dtype = df[col].dtype
#         nunique = df[col].nunique(dropna=True)
#         if pd.api.types.is_bool_dtype(dtype) or (pd.api.types.is_numeric_dtype(dtype) and nunique <= 2):
#             return 'boolean'
#         elif pd.api.types.is_datetime64_any_dtype(dtype):
#             return 'date'
#         elif pd.api.types.is_numeric_dtype(dtype):
#             return 'numeric'
#         else:
#             sample_idx = df[col].first_valid_index()
#             if sample_idx is not None:
#                 sample = df[col].loc[sample_idx]
#                 if isinstance(sample, str) and ('дат' in col.lower() or 'date' in col.lower() or 'time' in col.lower()):
#                     return 'date'
#             return 'categorical'

#     def safe_round(self, val, decimals=4):
#         return round(val, decimals) if pd.notna(val) else "NaN"

#     def generate_overview_page(self, df):
#         types = df.dtypes.astype(str)
#         omissions_count = df.isna().sum()
#         omissions_share = round((df.isna().sum() / df.shape[0]) * 100, 2)
#         unique_count = df.nunique()
#         not_nan_count = df.notna().sum()

#         info_df = pd.DataFrame({
#             'Признак': df.columns, 'Тип': types.values, 'Кол-во (not-null)': not_nan_count.values,
#             'Пропуски': omissions_count.values, 'Доля пропусков (%)': omissions_share.values, 'Уникальных': unique_count.values
#         })
#         dupes = df.duplicated().sum()
#         rows, cols = df.shape[0], df.shape[1]
#         idx_str = f"{df.index.start} по {df.index.stop - 1}" if isinstance(
#             df.index, pd.RangeIndex) else f"Index: {len(df)} entries"
#         mem_kb = df.memory_usage(deep=True).sum() / 1024
#         mem_str = f"{mem_kb:.1f}+ KB" if mem_kb < 1024 else f"{mem_kb/1024:.2f}+ MB"

#         dtypes_df = df.dtypes.astype(str).value_counts().reset_index()
#         dtypes_df.columns = ['Тип данных', 'Количество']

#         df_info = pd.DataFrame({
#             'Метрика': ['Количество строк', 'Индексы', 'Количество столбцов', 'Количество дубликатов', 'Используемая память'],
#             'Значение': [rows, f"с {idx_str}", cols, dupes, mem_str]
#         })

#         content = f"**Информация о датасете**\n\n```text\n{df_info.to_markdown(index=False)}\n```\n\n"
#         content += f"**Количество столбцов по типам**\n\n```text\n{dtypes_df.to_markdown(index=False)}\n```\n\n"
#         content += f"**Информация о столбцах**\n\n```text\n{info_df.to_markdown(index=False)}\n```\n"
#         return {'title': '📊 Обзор датасета', 'content': content}

#     def generate_sample_page(self, df):
#         sample_df = df.sample(min(17, len(df)), random_state=42)
#         content = f"\n```text\n{sample_df.to_markdown()}\n```\n\n"
#         return {'title': '📋 Случайные строки', 'content': content}

#     def generate_numeric_page(self, df, column):
#         series = df[column].dropna()
#         missing_count = df[column].isna().sum()

#         stats_df = pd.DataFrame({
#             'Метрика': [
#                 'Название столбца', 'Тип данных', 'Количество строк', 'Непустых',
#                 'Пропуски', 'Среднее', 'Медиана', 'Стандартное отклонение',
#                 'Минимум', 'Максимум', 'Асимметрия', 'Эксцесс'
#             ],
#             'Значение': [
#                 column, series.dtype, len(df), len(series),
#                 f"{missing_count} ({(missing_count / len(df)) * 100:.2f}%)",
#                 self.safe_round(series.mean()), self.safe_round(
#                     series.median()),
#                 self.safe_round(series.std()), self.safe_round(series.min()),
#                 self.safe_round(series.max()), self.safe_round(
#                     series.skew() if len(series) > 2 else np.nan),
#                 self.safe_round(series.kurt() if len(series) > 3 else np.nan)
#             ]
#         })

#         if series.empty:
#             return {'title': f"📈 Анализ: {column}", 'content': "### Нет данных для построения графика\n"}

#         fig = plt.figure(figsize=(16, 7))
#         # 33% ширины на таблицу (левая колонка), 67% на графики (правая колонка)
#         gs = fig.add_gridspec(2, 2, width_ratios=[
#                               0.33, 0.67], height_ratios=[0.75, 0.25])

#         ax_table = fig.add_subplot(gs[:, 0])
#         self._draw_table(ax_table, stats_df, title="Общие сведения")

#         ax_hist = fig.add_subplot(gs[0, 1])
#         sns.histplot(series, bins=30, ax=ax_hist, color="#2fa1a7",
#                      alpha=0.6, edgecolor="black", linewidth=0.5)
#         ax_hist.set_ylabel("Частота", fontsize=10)
#         ax_hist.set_xlabel("")
#         ax_hist.grid(color='gray', linestyle='-', alpha=0.3)
#         ax_kde = ax_hist.twinx()
#         sns.kdeplot(series, ax=ax_kde, color="#eb3472", linewidth=1.5)
#         ax_kde.set_yticks([])

#         ax_box = fig.add_subplot(gs[1, 1])
#         sns.boxplot(
#             x=series, ax=ax_box, color="#2fa1a7", width=0.4, linewidth=1, linecolor="black",
#             notch=True, fliersize=4, saturation=1, boxprops={'alpha': 0.6},
#             flierprops={'marker': 'o', 'markerfacecolor': '#eb3472',
#                         'markeredgecolor': 'none', 'alpha': 0.4}
#         )
#         ax_box.set_xlabel("Значение", fontsize=10)
#         ax_box.grid(color='gray', linestyle='-', alpha=0.3)

#         plt.tight_layout()
#         plot_md = self.convert_plot_to_md(fig, alt_text=f"Анализ {column}")
#         return {'title': f"📈 Анализ: {column}", 'content': f"{plot_md}\n"}

#     def generate_categorical_page(self, df, column):
#         series = df[column].dropna()
#         missing_count = df[column].isna().sum()
#         nunique = series.nunique()
#         rare_cats = (series.value_counts(normalize=True) < 0.01).sum()

#         stats_df = pd.DataFrame({
#             'Метрика': ['Название столбца', 'Тип данных', 'Количество строк', 'Пропуски', 'Уникальных', 'Высокая кардинальность (>50)', 'Редкие (<1%)'],
#             'Значение': [column, series.dtype, len(df), f"{missing_count} ({(missing_count / len(df)) * 100:.2f}%)", nunique, "Да ⚠" if nunique > 50 else "Нет", f"{rare_cats} шт."]
#         })

#         if series.empty:
#             return {'title': f"📈 Анализ: {column}", 'content': "### Нет данных для построения графика\n"}

#         fig = plt.figure(figsize=(16, 6))
#         gs = fig.add_gridspec(1, 2, width_ratios=[0.33, 0.67])

#         ax_table = fig.add_subplot(gs[0])
#         self._draw_table(ax_table, stats_df, title="Общие сведения")

#         ax_bar = fig.add_subplot(gs[1])
#         top_cats = series.value_counts().iloc[:15]
#         sns.barplot(y=top_cats.index.astype(str), x=top_cats.values, ax=ax_bar,
#                     hue=top_cats.index, legend=False, alpha=0.6, edgecolor="black", orient='h')
#         ax_bar.set_title("Частотный анализ (Топ-15)",
#                          fontsize=12, fontweight='bold')
#         ax_bar.set_xlabel("Количество", fontsize=10)
#         ax_bar.grid(color='gray', linestyle='-', alpha=0.3)

#         plt.tight_layout()
#         plot_md = self.convert_plot_to_md(fig, alt_text=f"Анализ {column}")
#         return {'title': f"📈 Анализ: {column}", 'content': f"{plot_md}\n"}

#     def generate_boolean_page(self, df, column):
#         series = df[column].dropna()
#         missing_count = df[column].isna().sum()
#         counts = series.value_counts()

#         stats_list = [['Название столбца', column], ['Тип данных', series.dtype], ['Количество строк', len(
#             df)], ['Пропуски', f"{missing_count} ({(missing_count / len(df)) * 100:.2f}%)"]]
#         for val, count in counts.items():
#             stats_list.append([f"Количество '{val}'", count])
#         stats_df = pd.DataFrame(stats_list, columns=['Метрика', 'Значение'])

#         if series.empty:
#             return {'title': f"📈 Анализ: {column}", 'content': "### Нет данных для построения графика\n"}

#         fig = plt.figure(figsize=(16, 6))
#         gs = fig.add_gridspec(1, 2, width_ratios=[0.33, 0.67])

#         ax_table = fig.add_subplot(gs[0])
#         self._draw_table(ax_table, stats_df, title="Общие сведения")

#         ax_pie = fig.add_subplot(gs[1])
#         colors = sns.color_palette('pastel')[0:len(counts)]
#         ax_pie.pie(counts.values, labels=counts.index, autopct='%1.1f%%', startangle=90,
#                    colors=colors, wedgeprops={'edgecolor': 'white', 'linewidth': 2})
#         ax_pie.add_artist(Circle((0, 0), 0.65, fc='white'))
#         ax_pie.set_title("Баланс классов", fontsize=12, fontweight='bold')

#         plt.tight_layout()
#         plot_md = self.convert_plot_to_md(fig, alt_text=f"Анализ {column}")
#         return {'title': f"📈 Анализ: {column}", 'content': f"{plot_md}\n"}

#     def generate_date_page(self, df, column):
#         empty_count = df[column].isna().sum()
#         dates = pd.to_datetime(df[column], errors='coerce')
#         invalid_count = dates.isna().sum() - empty_count
#         clean_dates = dates.dropna()

#         if clean_dates.empty:
#             return {'title': f"📈 Анализ: {column}", 'content': "### Нет корректных дат для графика\n"}

#         duration = clean_dates.max() - clean_dates.min()
#         stats_df = pd.DataFrame({
#             'Метрика': ['Название столбца', 'Тип данных', 'Количество строк', 'Пропуски', 'Некорректный формат', 'Начало периода', 'Конец периода', 'Продолжительность'],
#             'Значение': [column, df[column].dtype, len(df), empty_count, invalid_count, clean_dates.min().strftime('%Y-%m-%d'), clean_dates.max().strftime('%Y-%m-%d'), str(duration).split('.')[0]]
#         })

#         fig = plt.figure(figsize=(16, 6))
#         gs = fig.add_gridspec(1, 2, width_ratios=[0.33, 0.67])

#         ax_table = fig.add_subplot(gs[0])
#         self._draw_table(ax_table, stats_df, title="Общие сведения")

#         ax_hist = fig.add_subplot(gs[1])
#         sns.histplot(clean_dates, bins=30, ax=ax_hist, color="#2fa1a7",
#                      alpha=0.6, edgecolor="black", linewidth=0.5)
#         ax_kde = ax_hist.twinx()
#         sns.kdeplot(clean_dates, ax=ax_kde, color="#eb3472", linewidth=1.5)
#         ax_kde.set_yticks([])
#         ax_hist.set_title("Распределение во времени",
#                           fontsize=12, fontweight='bold')
#         ax_hist.grid(True, color='gray', linestyle='-', alpha=0.3)
#         plt.setp(ax_hist.xaxis.get_majorticklabels(), rotation=30, ha="right")

#         plt.tight_layout()
#         plot_md = self.convert_plot_to_md(fig, alt_text=f"Анализ {column}")
#         return {'title': f"📈 Анализ: {column}", 'content': f"{plot_md}\n"}

#     def build_eda_dashboard(self, title="Комплексный EDA Анализ"):
#         """Генерирует все страницы и выводит Markdown-аккордеон."""
#         print("⏳ Анализирую датасет и строю графики. Пожалуйста, подождите...")

#         pages = [
#             self.generate_overview_page(self._obj),
#             self.generate_sample_page(self._obj)
#         ]

#         for col in self._obj.columns:
#             col_type = self.get_column_type(self._obj, col)
#             if col_type == 'numeric':
#                 pages.append(self.generate_numeric_page(self._obj, col))
#             elif col_type == 'categorical':
#                 pages.append(self.generate_categorical_page(self._obj, col))
#             elif col_type == 'boolean':
#                 pages.append(self.generate_boolean_page(self._obj, col))
#             elif col_type == 'date':
#                 pages.append(self.generate_date_page(self._obj, col))

#         md_parts = [f"---\n\n## 📁 Датасет: {title}\n\n"]
#         for i, page in enumerate(pages):
#             is_open = 'open="open"' if i == 0 else ""
#             md_parts.append(f"""<details {is_open} style="margin-bottom: 10px; border: 1px solid #ddd; padding: 10px; border-radius: 5px;">
# <summary style="font-weight: bold; cursor: pointer; font-size: 1.1em; outline: none;">{page['title']}</summary>

# {page['content']}

# </details>
# <br>
# """)

#         clear_output()
#         display(Markdown("".join(md_parts)))
