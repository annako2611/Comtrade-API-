# 🎈 Додаток для отримання даних UN Comtrade API.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)

https://comtradeapi.streamlit.app/

## Загальний опис проекту

Цей веб-додаток, створений на базі фреймворку Streamlit, надає інтуїтивно зрозумілий інтерфейс для отримання, аналізу та візуалізації даних про торгівлю з Бази статистичних даних ООН по торгівлі товарами (UN Comtrade API). Додаток спеціально розроблений для запиту тарифних даних щодо імпорту України за різними товарними кодами та часовими періодами.

### Ключові функції

1. **Інтуїтивний користувацький інтерфейс**: Інтерфейс на базі Streamlit з елементами керування в бічній панелі для легкого вибору параметрів.
2. **Гнучкий вибір даних**: Користувачі можуть вибирати конкретні товарні коди та налаштовувати діапазони дат.
3. **Попередньо визначені приклади товарів**: Включає поширені товарні коди з описами для швидкого вибору.
4. **Багаторежимне представлення даних**:
   - Перегляд даних у табличному форматі з можливістю завантаження у CSV
   - Інтерактивні візуалізації даних з часовими рядами та середньомісячними значеннями
   - Перегляд у форматі JSON для структурованого аналізу даних
5. **Показники продуктивності**: Відстеження та відображення часу виконання API-запитів та статистики результатів.
6. **Експорт даних**: Дозволяє завантажувати отримані дані у форматі CSV та автоматично зберігає файли у форматі JSON.

### Цільові користувачі

- Аналітики зовнішньої торгівлі та економісти
- Державні установи, що моніторять імпортні потоки
- Дослідники, які вивчають торговельні дані України
- Фахівці з бізнес-аналітики
- Студенти та науковці у сфері міжнародної торгівлі та економіки

## Технічна документація

### Технологічний стек

- **Фронтенд і бекенд**: Фреймворк Streamlit
- **Обробка даних**: Pandas, NumPy
- **Візуалізація**: Matplotlib
- **Інтеграція з API**: Бібліотека Comtradeapicall
- **Формати даних**: JSON, CSV

### Структура коду та функціональність

#### Основні компоненти

1. **Налаштування додатку**
   ```python
   st.set_page_config(page_title="UN Comtrade Data Retrieval", layout="wide")
   st.title("UN Comtrade Tariff Line Data Retriever")
   ```
   Налаштовує макет додатку Streamlit та відображає заголовок і опис.

2. **Основна функція отримання даних**
   ```python
   def get_tariff_line_data(comtradeapicall, subscription_key, period_string, commodity_code):
   ```
   Це основна функція, яка:
   - Здійснює API-запити до UN Comtrade за допомогою бібліотеки comtradeapicall
   - Вимірює час виконання
   - Коректно обробляє помилки
   - Повертає як DataFrame Pandas, так і метадані результатів
   - Зберігає отримані дані у файли JSON

3. **Елементи керування користувацького інтерфейсу**
   - Введення ключа API (попередньо налаштоване зі стандартним ключем)
   - Вибір товарного коду з прикладами
   - Вибір діапазону дат з перевіркою
   - Генерація рядка періодів для API-запиту

4. **Фреймворк візуалізації даних**
   - Графік часового ряду, що показує значення імпорту за вибраний період
   - Стовпчаста діаграма середньомісячних значень, що показує сезонні патерни
   - Розрахунок та відображення зведеної статистики

#### Ключові секції коду

1. **Налаштування параметрів API**
   ```python
   panDForig = comtradeapicall._getTarifflineData(
       subscription_key, 
       typeCode='C',           # тип даних 
       freqCode='M',           # щомісячні дані
       clCode='HS',            # класифікація Harmonized System
       period=period_string,   # часовий період
       reporterCode=804,       # код України в UN Comtrade (804)
       cmdCode=commodity_code, # специфічний товарний код
       flowCode='M',           # напрямок торговельного потоку (Імпорт)
       ...
   )
   ```
   Налаштовує та виконує API-запит із конкретними параметрами для даних імпорту України.

2. **Логіка генерації періодів**
   ```python
   periods = pd.date_range(start=start_date, end=end_date, freq='MS').strftime("%Y%m").tolist()
   period_string = ",".join(periods)
   ```
   Генерує рядок значень рік-місяць, розділених комами, у форматі, необхідному для API UN Comtrade.

3. **Конвеєр візуалізації даних**
   ```python
   viz_data = panDForig.copy()
   viz_data['date'] = pd.to_datetime(viz_data['statPeriod'], format='%Y%m')
   viz_data = viz_data.sort_values('date')
   ```
   Перетворює необроблені дані API у формат, придатний для візуалізації часових рядів.

4. **Розрахунок середньомісячних значень**
   ```python
   monthly_avg = viz_data.groupby(viz_data['date'].dt.strftime('%B'))['primaryValue'].mean()
   ```
   Агрегує дані за місяцями для відображення сезонних патернів у значеннях імпорту.

### Структури даних

1. **Структура відповіді API**
   Додаток очікує, що API UN Comtrade повертатиме дані, які містять принаймні:
   - `statPeriod`: Часовий період у форматі YYYYMM
   - `primaryValue`: Значення торгівлі (зазвичай у доларах США)

2. **Метадані результатів**
   ```python
   results = {
       'commodity_code': commodity_code,
       'total_rows': len(panDForig),
       'execution_time': execution_time,
       'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
   }
   ```
   Фіксує метадані виконання для відстеження продуктивності та аудиту.

### Обробка помилок

Додаток реалізує комплексну обробку помилок:
- Збої з'єднання з API
- Перевірка недійсних параметрів
- Винятки обробки даних
- Збої візуалізації

### Вихідні файли

Додаток автоматично зберігає отримані дані у файли JSON з конвенцією іменування, яка включає:
- Товарний код
- Часову мітку отримання
Приклад: `tariff_data_310520_20230415_142530.json`

## Інструкції з використання

1. **Виберіть товарний код**:
   - Виберіть з попередньо визначених прикладів або введіть конкретний код HS
   
2. **Визначте часовий період**:
   - Виберіть початкову та кінцеву дати для періоду отримання даних
   
3. **Отримайте дані**:
   - Натисніть "Fetch Data", щоб ініціювати API-запит
   
4. **Досліджуйте результати**:
   - Перемикайтеся між вкладками "Data", "Visualization" та "JSON" для вивчення отриманої інформації
   - Завантажуйте дані у форматі CSV для подальшого аналізу
   - Вивчайте автоматично створені файли JSON для повних наборів даних

## Технічні вимоги

- Python 3.7+
- Необхідні пакети:
  - streamlit
  - pandas
  - matplotlib
  - numpy
  - comtradeapicall
  - python-dateutil

## Майбутні вдосконалення

Потенційні покращення для майбутніх версій:
1. Підтримка кількох товарних кодів в одному запиті
2. Порівняльний аналіз між різними часовими періодами
3. Додаткові типи візуалізації (географічні карти, аналіз країн-партнерів)
4. Розширені опції фільтрації та трансформації даних
5. Інтеграція з базою даних для зберігання історичних запитів
6. Експорт у додаткові формати (Excel, PDF-звіти)
7. Вдосконалені механізми відновлення після помилок та повторних спроб

## UKR Дослідницький проєкт: Імпорт NPK добрив у цифрах: аналіз тенденцій та географії

## Вступ
Проєкт присвячено аналізу імпорту NPK добрив до України. Цей проєкт має на меті визначення основних імпортерів NPK добрив, динаміки імпорту протягом періоду 2019–2025 років та основних джерел імпорту.

## Огляд даних
У цьому проєкті аналіз даних базується на джерелі: https://comtradeplus.un.org/, яке надало CSV-файли на основі кодів Гармонізованої системи (HS) 310520 (добрива мінеральні або хімічні, що містять три елементи, які удобрюють: азот, фосфор і калій).

## 1. Аналіз тенденцій імпорту

Як змінювався обсяг імпорту NPK за роками?
Які сезонні тенденції спостерігаються в імпорті (аналіз по місяцях)?

## 2. Географічний аналіз

Які країни є найбільшими імпортерами та експортерами NPK?
Як змінювались торгові потоки між країнами за досліджуваний період?

## 3. Аналіз товарної структури

Які типи NPK-добрив найбільш популярні в імпорті?
Чи є зміни у структурі імпортованих товарів за досліджуваний період?

## ENG Research project: Imports of NPK fertilisers in numbers: trend and geographical analysis

## Introduction
The project is dedicated to the analysis of the import of NPK fertilizers into Ukraine. This project aims to define the main importers of NPK fertilizers, tthe dynamics of imports throughout the period 2019–2025, and the main sources of import.

## Data Overview
In this project, the data analysis the data analysis relies on the source: https://comtradeplus.un.org/ , which has provided CSV files based on HS (Harmonized System) code 310520 (fertilizers, mineral or chemical, containing the three fertilizing elements nitrogen, phosphorus, and potassium).

## 1. Analysis of import trends

How has the volume of NPK imports changed over the years?
What are the seasonal trends in imports (monthly analysis)?

## 2. Geographical analysis

Which countries are the largest importers and exporters of NPK?
How did trade flows between countries change during the study period?

## 3. Product structure analysis

What types of NPK fertilisers are most popular for import?
Have there been any changes in the structure of imported goods during the study period?
