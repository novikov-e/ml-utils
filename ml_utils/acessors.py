import base64
import io
from jinja2 import Template, Environment, FileSystemLoader
from pathlib import Path
import html

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from IPython.display import clear_output, display, Markdown
from ipywidgets import HTML, Button, HBox, Layout, VBox
from matplotlib.patches import Circle

if '__file__' in globals():
    BASE_DIR = Path(__file__).parent
else:
    BASE_DIR = Path.cwd()

@pd.api.extensions.register_dataframe_accessor("eda_utils")
class CleanerAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj
        self._css = self._read_asset('static/styles.css')
        self.jinja_env = Environment(loader=FileSystemLoader(BASE_DIR))

    def _read_asset(self, filename: str) -> str:
        """Читает содержимое HTML/CSS файла по относительному пути."""
        file_path = BASE_DIR / filename
        if not file_path.exists():
            return f"<!-- ВНИМАНИЕ: Файл {filename} не найден по пути {file_path} -->"
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def convert_plot_to_html(self, fig):
        """Конвертирует объект matplotlib figure в центрированную HTML-строку с собственным скроллом."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
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
        self._page_tpl = Template(self._read_asset('static/page-layout.html'))
        return self._page_tpl.render(
            left_html=left_html,
            right_html=right_html
        )

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

        # 1. Данные для таблицы "Информация о столбцах" (Правая колонка)
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

        # 2. Данные для таблицы "Информация о датасете" (Левая колонка, верх)
        dupes = df.duplicated().sum()
        rows, cols = df.shape[0], df.shape[1]
        idx_str = f"{df.index.start} по {df.index.stop - 1}" if isinstance(
            df.index, pd.RangeIndex) else f"Index: {len(df)} entries"
        mem_bytes = df.memory_usage(deep=True).sum()
        mem_kb = mem_bytes / 1024
        mem_str = f"{mem_kb:.1f}+ KB" if mem_kb < 1024 else f"{mem_kb/1024:.2f}+ MB"

        df_info = pd.DataFrame({
            'Метрика': ['Количество строк', 'Индексы', 'Количество столбцов', 'Количество дубликатов', 'Используемая память'],
            'Значение': [rows, f"с {idx_str}", cols, dupes, mem_str]
        })

        # 3. Данные для таблицы "Количество столбцов по типам" (Левая колонка, низ)
        dtypes_df = df.dtypes.astype(str).value_counts().reset_index()
        dtypes_df.columns = ['Тип данных', 'Количество']

        # 4. Рендеринг единого шаблона
        # Используем ранее созданную глобальную функцию read_asset
        tpl = self.jinja_env.get_template('static/overview.html')

        full_page_html = tpl.render(
            # Передаем таблицу столбцов
            info_cols=info_df.columns.tolist(),
            info_rows=info_df.astype(str).to_dict(orient='records'),
            align_info={'Признак': 'left', 'Тип': 'center',
                        'Кол-во (not-null)': 'center', 'Пропуски': 'center', 'Доля пропусков (%)': 'center', 'Уникальных': 'center'},

            # Передаем таблицу общих метрик
            df_info_cols=df_info.columns.tolist(),
            df_info_rows=df_info.astype(str).to_dict(orient='records'),
            align_df_info={'Метрика': 'left', 'Значение': 'center'},

            # Передаем таблицу типов данных
            dtypes_cols=dtypes_df.columns.tolist(),
            dtypes_rows=dtypes_df.astype(str).to_dict(orient='records'),
            align_dtypes={'Тип данных': 'left', 'Количество': 'center'}
        )

        return {'title': 'Обзор датасета', 'content': full_page_html}

    def generate_sample_page(self, df):
        """Создает страницу со случайными строками для ознакомления с данными."""
        sample_size = min(17, len(df))
        sample_df = df.sample(sample_size, random_state=42)

        # 1. Подготавливаем списки и словари для шаблонизатора
        columns = sample_df.columns.tolist()
        rows = sample_df.astype(str).to_dict(orient='records')

        # Задаем выравнивание по левому краю для всех колонок
        # (в макросе по умолчанию стоит center, поэтому переопределяем явно)
        align_sample = {col: 'left' for col in columns}

        # 2. Рендерим шаблон через уже настроенное окружение
        tpl = self.jinja_env.get_template('static/sample.html')

        full_page_html = tpl.render(
            columns=columns,
            rows=rows,
            aligns=align_sample
        )

        return {'title': 'Случайные строки', 'content': full_page_html}

    def generate_numeric_page(self, df, column):
        """Анализ числового признака (Гистограмма + Ящик с усами)."""
        series = df[column].dropna()
        missing_count = df[column].isna().sum()
        missing_percent = (missing_count / len(df)) * 100

        # 1. Формируем DataFrame со статистикой
        stats_df = pd.DataFrame({
            'Метрика': [
                'Название столбца', 'Тип данных', 'Количество строк', 'Непустых',
                'Пропуски', 'Среднее', 'Медиана', 'Стандартное отклонение',
                'Минимум', 'Максимум', 'Асимметрия', 'Эксцесс'
            ],
            'Значение': [
                column, series.dtype, len(df), len(series),
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

        # 2. Подготавливаем данные таблицы для Jinja2
        stats_cols = stats_df.columns.tolist()
        stats_rows = stats_df.astype(str).to_dict(orient='records')
        align_stats = {'Метрика': 'left', 'Значение': 'center'}

        # 3. Генерируем график
        if series.empty:
            plot_html = "<div style='text-align:center; width:100%;'><h3>Нет данных для построения графика</h3></div>"
        else:
            with plt.style.context('default'):
                fig, axes = plt.subplots(
                    nrows=2, ncols=1, figsize=(7.5, 4.5),
                    gridspec_kw={"height_ratios": [0.8, 0.2]}
                )

                sns.histplot(
                    series, bins=30, ax=axes[0], color="#2fa1a7", alpha=0.6, edgecolor="black", linewidth=0.5)
                axes[0].set_ylabel("Частота", fontsize=9)
                axes[0].set_xlabel("")
                axes[0].grid(color='gray', linestyle='-', alpha=0.3)
                axes[0].set_axisbelow(False)

                ax_kde = axes[0].twinx()
                sns.kdeplot(series, ax=ax_kde, color="#eb3472", linewidth=1)
                ax_kde.set_ylabel("")
                ax_kde.set_yticks([])

                sns.boxplot(
                    x=series, ax=axes[1], color="#2fa1a7", width=0.4, linewidth=1,
                    linecolor="black", notch=True, fliersize=4, saturation=1,
                    boxprops={'alpha': 0.6}, flierprops={'marker': 'o', 'markerfacecolor': '#eb3472', 'markeredgecolor': 'none', 'alpha': 0.4}
                )
                axes[1].set_xlabel("Значение", fontsize=9)
                axes[1].grid(color='gray', linestyle='-', alpha=0.3)
                axes[1].set_axisbelow(False)

                plt.tight_layout()
                plot_html = self.convert_plot_to_html(fig)

        # 4. Рендерим шаблон
        tpl = self.jinja_env.get_template('static/column_page.html')
        full_page_html = tpl.render(
            stats_cols=stats_cols,
            stats_rows=stats_rows,
            align_stats=align_stats,
            plot_html=plot_html
        )

        return {'title': f"Столбец {column}", 'content': full_page_html}

    def generate_categorical_page(self, df, column):
        """Анализ категориального признака (Частотный анализ, редкие категории)."""
        series = df[column].dropna()

        missing_count = df[column].isna().sum()
        missing_percent = (missing_count / len(df)) * 100
        nunique = series.nunique()
        counts = series.value_counts(normalize=True)
        rare_cats_count = (counts < 0.01).sum()

        # 1. Формируем DataFrame со статистикой
        stats_df = pd.DataFrame({
            'Метрика': [
                'Название столбца',
                'Тип данных',
                'Количество строк',
                'Пропуски',
                'Уникальных значений',
                'Высокая кардинальность (>50)',
                'Редкие категории (<1%)'
            ],
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

        # 2. Подготавливаем данные таблицы для Jinja2
        stats_cols = stats_df.columns.tolist()
        stats_rows = stats_df.astype(str).to_dict(orient='records')
        align_stats = {'Метрика': 'left', 'Значение': 'center'}

        # 3. Генерируем график
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

        # 4. Рендерим универсальный шаблон столбца
        tpl = self.jinja_env.get_template('static/column_page.html')
        full_page_html = tpl.render(
            stats_cols=stats_cols,
            stats_rows=stats_rows,
            align_stats=align_stats,
            plot_html=plot_html
        )

        return {'title': f"Столбец {column}", 'content': full_page_html}

    def generate_boolean_page(self, df, column):
        """Анализ логического/бинарного признака (Дисбаланс классов)."""
        series = df[column].dropna()

        missing_count = df[column].isna().sum()
        missing_percent = (missing_count / len(df)) * 100
        counts = series.value_counts()

        # 1. Формируем DataFrame со статистикой
        stats_list = [
            ['Название столбца', column],
            ['Тип данных', series.dtype],
            ['Количество строк', len(df)],
            ['Пропуски', f"{missing_count} ({missing_percent:.2f}%)"]
        ]
        for val, count in counts.items():
            stats_list.append([f"Количество '{val}'", count])

        stats_df = pd.DataFrame(stats_list, columns=['Метрика', 'Значение'])

        # 2. Подготавливаем данные таблицы для Jinja2
        stats_cols = stats_df.columns.tolist()
        stats_rows = stats_df.astype(str).to_dict(orient='records')
        align_stats = {'Метрика': 'left', 'Значение': 'center'}

        # 3. Генерируем график
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

        # 4. Рендерим универсальный шаблон столбца
        tpl = self.jinja_env.get_template('static/column_page.html')
        full_page_html = tpl.render(
            stats_cols=stats_cols,
            stats_rows=stats_rows,
            align_stats=align_stats,
            plot_html=plot_html
        )

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
            # 1. Если корректных дат нет, формируем таблицу с ошибкой
            stats_df = pd.DataFrame({
                'Метрика': ['Ошибка'],
                'Значение': ['Нет дат']
            })
            plot_html = "<div style='text-align:center; width:100%;'><h3>Нет корректных дат</h3></div>"
        else:
            # 2. Если даты есть, формируем полноценную таблицу со статистикой
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

            # Генерируем график
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

        # 3. Подготавливаем данные таблицы для Jinja2 (работает для обоих сценариев)
        stats_cols = stats_df.columns.tolist()
        stats_rows = stats_df.astype(str).to_dict(orient='records')

        # 4. Рендерим универсальный шаблон столбца
        tpl = self.jinja_env.get_template('static/column_page.html')
        full_page_html = tpl.render(
            stats_cols=stats_cols,
            stats_rows=stats_rows,
            align_stats=align_stats,
            plot_html=plot_html
        )

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

        # Жесткая защита стилей кнопок от темной темы Colab/VS Code
        btn_prev.style.button_color = '#f2f2f2'
        btn_prev.style.text_color = '#212121'
        btn_next.style.button_color = '#f2f2f2'
        btn_next.style.text_color = '#212121'

        # Загружаем шаблон шапки один раз
        header_tpl = self.jinja_env.get_template('static/header.html')

        def update_state():
            idx = current_page_idx[0]
            page = pages[idx]

            # Используем Jinja2 для рендера шапки
            header_widget.value = header_tpl.render(
                main_title=title,
                page_title=page['title'],
                current_page=idx + 1,
                total_pages=total_pages
            )

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

        top_panel = HBox([header_widget, btn_prev, btn_next], layout=Layout(
            display='flex', justify_content='space-between', align_items='center',
            padding='5px 10px', border_bottom='1px solid #ddd', margin='0px 0px 15px 0px', width='100%'))

        global_styles = HTML(value=f"<style>\n{self._css}\n</style>")

        dashboard_layout = VBox(
            [global_styles, top_panel, content_widget],
            layout=Layout(display='flex', flex_direction='column',
                          width='100%', height='auto', overflow='hidden')
        )

        # Применяем изолирующий класс ко всем основным виджетам
        dashboard_layout.add_class('dashboard-wrapper')
        top_panel.add_class('dashboard-wrapper')
        content_widget.add_class('dashboard-wrapper')

        clear_output()
        display(dashboard_layout)

    
