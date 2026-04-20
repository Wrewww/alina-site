import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
import base64


def create_calories_chart(meal_data, daily_norm):
    """График сравнения калорий с нормой"""
    try:
        fig, ax = plt.subplots(figsize=(10, 5))

        meal_types = ['Завтрак', 'Обед', 'Ужин']
        calories = [
            meal_data.get('breakfast', {}).get('total_calories', 0),
            meal_data.get('lunch', {}).get('total_calories', 0),
            meal_data.get('dinner', {}).get('total_calories', 0)
        ]
        total_calories = sum(calories)

        x = np.arange(len(meal_types))
        bars = ax.bar(x, calories, color='#81C784', edgecolor='#2E7D32', linewidth=2)

        ax.axhline(y=daily_norm, color='#2E7D32', linestyle='--', linewidth=2,
                   label=f'Норма ({daily_norm} ккал)', alpha=0.8)

        ax.set_ylabel('Калории (ккал)', fontsize=12)
        ax.set_title(f'Калории за день • Всего: {total_calories:.0f} / {daily_norm} ккал',
                     fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(meal_types)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3, axis='y')

        for bar, val in zip(bars, calories):
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                        f'{val:.0f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        image = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        return image
    except Exception as e:
        print(f"Ошибка в calories chart: {e}")
        return ""


def create_nutrients_chart(proteins, fats, carbs):
    """Круговая диаграмма БЖУ - принимает три аргумента"""
    try:
        fig, ax = plt.subplots(figsize=(7, 7))

        labels = ['Белки', 'Жиры', 'Углеводы']
        sizes = [proteins, fats, carbs]
        colors = ['#FF9800', '#2196F3', '#4CAF50']

        # Убираем нулевые значения
        non_zero = [(l, s, c) for l, s, c in zip(labels, sizes, colors) if s > 0]

        if non_zero:
            labels, sizes, colors = zip(*non_zero)

            def autopct_func(pct):
                total = sum(sizes)
                val = int(round(pct * total / 100.0))
                return f'{pct:.1f}%\n({val} г)'

            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors,
                                              autopct=autopct_func, startangle=90,
                                              textprops={'fontsize': 11, 'fontweight': 'bold'})

            for autotext in autotexts:
                autotext.set_color('white')

            ax.set_title('Распределение БЖУ', fontsize=14, fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'Нет данных за сегодня', ha='center', va='center',
                    fontsize=12, transform=ax.transAxes)
            ax.set_title('Распределение БЖУ', fontsize=14, fontweight='bold')

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        image = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        return image
    except Exception as e:
        print(f"Ошибка в nutrients chart: {e}")
        return ""


def create_weekly_chart(weekly_calories, days):
    """Недельный график калорий"""
    try:
        fig, ax = plt.subplots(figsize=(12, 5))

        ax.plot(days, weekly_calories, marker='o', linewidth=2, markersize=8,
                color='#2E7D32', markerfacecolor='white', markeredgewidth=2)
        ax.fill_between(days, weekly_calories, alpha=0.3, color='#81C784')

        ax.set_xlabel('Дата', fontsize=12)
        ax.set_ylabel('Калории (ккал)', fontsize=12)
        ax.set_title('Динамика калорий за неделю', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)

        for i, v in enumerate(weekly_calories):
            if v > 0:
                ax.text(i, v + max(weekly_calories) * 0.02, f'{v:.0f}',
                        ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        image = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        return image
    except Exception as e:
        print(f"Ошибка в weekly chart: {e}")
        return ""


def create_meals_chart(meal_calories):
    """График калорий по приемам пищи"""
    try:
        fig, ax = plt.subplots(figsize=(8, 6))

        meal_types = ['Завтрак', 'Обед', 'Ужин']
        calories = [
            meal_calories.get('breakfast', 0),
            meal_calories.get('lunch', 0),
            meal_calories.get('dinner', 0)
        ]

        colors = ['#FF9800', '#2196F3', '#4CAF50']
        bars = ax.bar(meal_types, calories, color=colors, edgecolor='white', linewidth=2)

        ax.set_ylabel('Калории (ккал)', fontsize=12)
        ax.set_title('Распределение калорий по приемам пищи', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        for bar, val in zip(bars, calories):
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                        f'{val:.0f}', ha='center', va='bottom', fontsize=12, fontweight='bold')

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        image = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        return image
    except Exception as e:
        print(f"Ошибка в meals chart: {e}")
        return ""