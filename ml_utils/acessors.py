import base64
import io
import json
import time
import uuid
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from IPython.display import HTML, clear_output, display
from jinja2 import Environment, FileSystemLoader
from matplotlib.patches import Circle

if '__file__' in globals():
    BASE_DIR = Path(__file__).parent
else:
    BASE_DIR = Path.cwd()


@pd.api.extensions.register_dataframe_accessor("eda_utils")
class CleanerAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj
        self.jinja_env = Environment(
            loader=FileSystemLoader(BASE_DIR / 'static'))

    def _read_asset(self, filename: str) -> str:
        """Читает содержимое файла по относительному пути."""
        file_path = BASE_DIR / filename
        if not file_path.exists():
            return f"<!-- ВНИМАНИЕ: Файл {filename} не найден -->"
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _build_html_table(self, cols, rows, aligns=None):
        """Внутренний метод для генерации HTML-таблиц через Jinja2."""
        if aligns is None:
            aligns = {}

        clean_rows = []
        for row in rows:
            clean_row = {}
            for c in cols:
                val = row.get(c, '')
                val_str = ("" if not isinstance(val, str)
                           and pd.isna(val) else str(val))
                if val_str.lower() == 'nan':
                    val_str = ""
                clean_row[c] = val_str
            clean_rows.append(clean_row)

        template = self.jinja_env.get_template('table.html')
        return template.render(
            cols=cols,
            rows=clean_rows,
            aligns=aligns
        )

    def convert_plot_to_html(self, fig):
        """Конвертирует объект matplotlib figure в HTML img через Jinja2."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)

        template = self.jinja_env.get_template('image.html')
        return template.render(img_base64=img_base64)

    def get_column_type(self, df, col):
        dtype = df[col].dtype
        nunique = df[col].nunique(dropna=True)

        if (pd.api.types.is_bool_dtype(dtype)
                or (pd.api.types.is_numeric_dtype(dtype) and nunique <= 2)):
            return 'boolean'
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return 'date'
        elif pd.api.types.is_numeric_dtype(dtype):
            return 'numeric'
        else:
            sample_idx = df[col].first_valid_index()
            if sample_idx is not None:
                sample = str(df[col].loc[sample_idx])
                if len(sample) >= 6:
                    try:
                        # Если pandas может распарсить эту строку как дату без ошибок
                        pd.to_datetime(sample)
                        return 'date'
                    except (ValueError, TypeError, pd.errors.ParserError):
                        pass

            return 'categorical'

    def safe_round(self, val, decimals=4):
        return round(val, decimals) if pd.notna(val) else "NaN"

    def generate_overview_page(self, df):
        types = df.dtypes.astype(str)
        omissions_count = df.isna().sum()
        omissions_share = round((df.isna().sum() / df.shape[0]) * 100, 2)
        unique_count = df.nunique()
        not_nan_count = df.notna().sum()

        info_df = pd.DataFrame({
            'Признак': df.columns,
            'Тип': types.values,
            'Кол-во': not_nan_count.values,
            'Пропуски': omissions_count.values,
            'Доля пропусков (%)': omissions_share.values,
            'Уникальных': unique_count.values
        })

        dupes = df.duplicated().sum()
        rows, cols = df.shape[0], df.shape[1]
        idx_str = f"{df.index.start} по {df.index.stop - 1}" if isinstance(
            df.index, pd.RangeIndex) else f"Index: {len(df)} entries"
        mem_bytes = df.memory_usage(deep=True).sum()
        mem_kb = mem_bytes / 1024
        mem_str = f"{mem_kb:.1f}+ KB" if mem_kb < 1024 else f"{mem_kb/1024:.2f}+ MB"

        df_info = pd.DataFrame({
            'Метрика': [
                'Количество строк',
                'Индексы',
                'Количество столбцов',
                'Количество дубликатов',
                'Используемая память'],
            'Значение': [
                rows,
                f"с {idx_str}",
                cols,
                dupes,
                mem_str]
        })

        dtypes_df = df.dtypes.astype(str).value_counts().reset_index()
        dtypes_df.columns = ['Тип данных', 'Количество']

        html_df_info = self._build_html_table(
            df_info.columns.tolist(),
            df_info.astype(str).to_dict('records')
        )
        html_dtypes = self._build_html_table(
            dtypes_df.columns.tolist(),
            dtypes_df.astype(str).to_dict('records')
        )
        html_info = self._build_html_table(
            info_df.columns.tolist(), info_df.astype(str).to_dict('records'),
            aligns={'Признак': 'left',
                    'Тип': 'center',
                    'Кол-во': 'center',
                    'Пропуски': 'center',
                    'Доля пропусков (%)': 'center',
                    'Уникальных': 'center'}
        )

        template = self.jinja_env.get_template('overview.html')
        content = template.render(
            html_df_info=html_df_info,
            html_dtypes=html_dtypes,
            html_info=html_info
        )

        return {'title': 'Обзор датасета', 'content': content}

    def generate_sample_page(self, df):
        sample_size = min(18, len(df))
        sample_df = df.sample(sample_size, random_state=42)
        columns = sample_df.columns.tolist()
        rows = sample_df.astype(str).to_dict(orient='records')
        table_html = self._build_html_table(columns, rows)
        template = self.jinja_env.get_template('sample.html')
        content = template.render(table_html=table_html)
        return {'title': 'Случайные строки', 'content': content}

    def _render_column_layout(self, stats_df, plot_html):
        stats_html = self._build_html_table(
            stats_df.columns.tolist(),
            stats_df.astype(str).to_dict('records')
        )
        template = self.jinja_env.get_template('column_layout.html')
        return template.render(
            stats_html=stats_html,
            plot_html=plot_html
        )

    def generate_numeric_page(self, df, column):
        series = df[column].dropna()
        missing_count = df[column].isna().sum()
        missing_percent = (missing_count / len(df)) * 100
        nunique = series.nunique()

        stats_df = pd.DataFrame({
            'Метрика': [
                'Название столбца',
                'Тип данных',
                'Количество строк',
                'Непустых',
                'Пропуски',
                'Уникальных значений',
                'Среднее',
                'Медиана',
                'Стандартное отклонение',
                'Минимум',
                'Максимум',
                'Асимметрия',
                'Эксцесс'
            ],
            'Значение': [
                column,
                series.dtype,
                len(df),
                len(series),
                f"{missing_count} ({missing_percent:.2f}%)",
                nunique,
                self.safe_round(series.mean()),
                self.safe_round(series.median()),
                self.safe_round(series.std()),
                self.safe_round(series.min()),
                self.safe_round(series.max()),
                self.safe_round(series.skew() if len(series) > 2 else np.nan),
                self.safe_round(series.kurt() if len(series) > 3 else np.nan)
            ]
        })

        if series.empty:
            plot_html = """
            <div class='image-container' style='align-items:center;'>
                <h3>Нет данных для построения графика</h3>
            </div>"""
        else:
            with plt.style.context('default'):
                fig, axes = plt.subplots(nrows=2,
                                         ncols=1,
                                         figsize=(7.5, 4.5),
                                         gridspec_kw={"height_ratios": [0.8, 0.2]})

                is_discrete = nunique < 25

                if is_discrete:
                    sns.histplot(series,
                                 discrete=True,
                                 ax=axes[0],
                                 color="#2fa1a7",
                                 alpha=0.6,
                                 edgecolor="black",
                                 linewidth=0.5)
                else:
                    sns.histplot(series,
                                 bins='auto',
                                 ax=axes[0],
                                 color="#2fa1a7",
                                 alpha=0.6,
                                 edgecolor="black",
                                 linewidth=0.5)

                    if series.var() > 0:
                        ax_kde = axes[0].twinx()
                        sns.kdeplot(series,
                                    ax=ax_kde,
                                    color="#eb3472",
                                    linewidth=1,
                                    warn_singular=False)
                        ax_kde.set_ylabel("")
                        ax_kde.set_yticks([])

                axes[0].set_ylabel("Частота", fontsize=9)
                axes[0].set_xlabel("")
                axes[0].grid(color='gray', linestyle='-', alpha=0.3)
                axes[0].set_axisbelow(False)
                axes[0].set_title("Распределение значений",
                                  fontsize=11, 
                                  fontweight='bold')
                sns.boxplot(x=series,
                            ax=axes[1],
                            color="#2fa1a7",
                            width=0.4,
                            linewidth=1,
                            linecolor="black",
                            notch=True,
                            fliersize=4)
                axes[1].set_xlabel("Значение", fontsize=9)
                axes[1].grid(color='gray', linestyle='-', alpha=0.3)
                axes[1].set_axisbelow(False)

                plt.tight_layout()
                plot_html = self.convert_plot_to_html(fig)

        content = self._render_column_layout(stats_df, plot_html)
        return {'title': column, 'content': content}

    def generate_categorical_page(self, df, column):
        series = df[column].dropna()
        missing_count = df[column].isna().sum()
        missing_percent = (missing_count / len(df)) * 100
        nunique = series.nunique()
        counts = series.value_counts(normalize=True)
        rare_cats_count = (counts < 0.01).sum()

        stats_df = pd.DataFrame({
            'Метрика': [
                'Название',
                'Тип',
                'Всего строк',
                'Пропуски',
                'Уникальных',
                'Высокая кардинальность (>50)',
                'Редкие (<1%)'],
            'Значение': [
                column,
                series.dtype,
                len(df),
                f"{missing_count} ({missing_percent:.2f}%)",
                nunique,
                "Да ⚠️" if nunique > 50 else "Нет",
                f"{rare_cats_count} шт."]
        })

        if series.empty:
            plot_html = "<div class='image-container' style='align-items:center;'><h3>Нет данных</h3></div>"
        else:
            with plt.style.context('default'):
                fig, ax = plt.subplots(figsize=(7.5, 4.5))
                top_cats = series.value_counts().iloc[:15]
                sns.barplot(y=top_cats.index.astype(str),
                            x=top_cats.values,
                            ax=ax,
                            hue=top_cats.index,
                            legend=False,
                            alpha=0.6,
                            edgecolor="black",
                            orient='h')
                ax.set_title(f"Распределение категорий",
                             fontsize=11,
                             fontweight='bold')
                ax.set_xlabel("Количество", fontsize=9)
                ax.grid(color='gray', linestyle='-', alpha=0.3)
                plt.tight_layout()
                plot_html = self.convert_plot_to_html(fig)

        content = self._render_column_layout(stats_df, plot_html)
        return {'title': column, 'content': content}

    def generate_boolean_page(self, df, column):
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
            stats_list.append([f"Кол-во '{val}'", count])

        stats_df = pd.DataFrame(stats_list, columns=['Метрика', 'Значение'])

        if series.empty:
            plot_html = "<div class='image-container' style='align-items:center;'><h3>Нет данных</h3></div>"
        else:
            with plt.style.context('default'):
                fig, ax = plt.subplots(figsize=(7.5, 4.5))
                colors = sns.color_palette('pastel')[0:len(counts)]
                ax.pie(counts.values,
                       labels=counts.index,
                       autopct='%1.1f%%',
                       startangle=90,
                       colors=colors,
                       wedgeprops={'edgecolor': 'white', 'linewidth': 2})
                centre_circle = Circle((0, 0), 0.65, fc='white')
                fig.gca().add_artist(centre_circle)
                ax.axis('equal')
                ax.set_title(f"Баланс классов", fontsize=11, fontweight='bold')
                plt.tight_layout()
                plot_html = self.convert_plot_to_html(fig)

        content = self._render_column_layout(stats_df, plot_html)
        return {'title': column, 'content': content}

    def generate_date_page(self, df, column):
        empty_count = df[column].isna().sum()
        dates = pd.to_datetime(df[column], errors='coerce')
        invalid_count = dates.isna().sum() - empty_count
        clean_dates = dates.dropna()

        if clean_dates.empty:
            stats_df = pd.DataFrame({
                'Метрика': ['Ошибка'],
                'Значение': ['Нет корректных дат']})
            plot_html = """
            <div class='image-container' style='align-items:center;'>
                <h3>Нет дат</h3>
            </div>"""
        else:
            duration = clean_dates.max() - clean_dates.min()
            stats_df = pd.DataFrame({
                'Метрика': [
                    'Название',
                    'Тип',
                    'Строк',
                    'Пропуски',
                    'Некорректный формат',
                    'Начало',
                    'Конец',
                    'Продолжительность'],
                'Значение': [
                    column,
                    df[column].dtype,
                    len(df),
                    empty_count,
                    invalid_count,
                    clean_dates.min().strftime('%Y-%m-%d'),
                    clean_dates.max().strftime('%Y-%m-%d'),
                    str(duration).split('.')[0]]
            })

            with plt.style.context('default'):
                fig, ax = plt.subplots(figsize=(7.5, 4.5))
                sns.histplot(clean_dates,
                             bins=30,
                             ax=ax,
                             color="#2fa1a7",
                             alpha=0.6,
                             edgecolor="black")
                ax_kde = ax.twinx()
                sns.kdeplot(clean_dates,
                            ax=ax_kde,
                            color="#eb3472",
                            linewidth=1)
                ax_kde.set_yticks([])
                ax.set_title(f"Распределение во времени",
                             fontsize=11,
                             fontweight='bold')
                ax.grid(True, color='gray', linestyle='-', alpha=0.3)
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                plt.tight_layout()
                plot_html = self.convert_plot_to_html(fig)

        content = self._render_column_layout(stats_df, plot_html)
        return {'title': column, 'content': content}

    def build_eda_dashboard(self, title="Комплексный EDA Анализ"):
        print("⏳ Анализ датасета и построение графиков. Пожалуйста, подождите...")

        pages = []
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

        dash_id = str(uuid.uuid4())[:8]
        page_titles = [p['title'] for p in pages]
        pages_html = []
        for i, page in enumerate(pages):
            display_style = "block" if i == 0 else "none"
            pages_html.append(
                f'<div id="eda-page-{dash_id}-{i}" class="eda-page" style="display: {display_style};">{page["content"]}</div>')
        pages_html_str = "".join(pages_html)
        titles_json = json.dumps(page_titles)

        css_content = self._read_asset('static/styles.css')
        js_template = self.jinja_env.get_template('script.js')
        js_content = js_template.render(
            TOTAL_PAGES=len(pages),
            DASH_ID=dash_id,
            TITLES_JSON=titles_json
        )
        layout_template = self.jinja_env.get_template('layout.html')
        final_html = layout_template.render(
            STYLES=css_content,
            SCRIPT=js_content,
            DASH_ID=dash_id,
            TITLE=title,
            PAGE_TITLE=page_titles[0],
            TOTAL_PAGES=len(pages),
            CONTENT=pages_html_str
        )

        clear_output()
        display(HTML(final_html))
        time.sleep(2.0)
