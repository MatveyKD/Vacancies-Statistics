import os
from itertools import count

import requests
from terminaltables import AsciiTable
from dotenv import load_dotenv


def predict_salary(from_salary, to_salary):
    if from_salary:
        if to_salary:
            return (from_salary + to_salary) / 2
        return from_salary * 1.2
    elif to_salary:
        return to_salary * 0.8


def predict_rub_salary_hh(vacancy):
    if vacancy["salary"]:
        from_salary = vacancy["salary"]["from"]
        to_salary = vacancy["salary"]["to"]
        valute = vacancy["salary"]["currency"]
        if valute == "RUR":
            return predict_salary(from_salary, to_salary)


def predict_rub_salary_sj(vacancy):
    payment_from = vacancy["payment_from"]
    payment_to = vacancy["payment_to"]
    valute = vacancy["currency"]
    if valute == "rub":
        return predict_salary(payment_from, payment_to)


def get_language_stats_hh(language):
    found = 0
    processed = 0
    average = 0

    url = "https://api.hh.ru/vacancies"

    for page in count(0):
        payload = {
            "text": f"Программист {language}",
            "area": 1,
            "page": page,
            "per_page": 100
        }

        response = requests.get(url, params=payload)
        response.raise_for_status()
                
        res_json = response.json()
        for vacancy in res_json["items"]:
            salary = predict_rub_salary_hh(vacancy)
            if salary:
                average += salary
                processed += 1
        found += res_json["found"]

        if page >= res_json['pages'] - 1:
                break

    if processed:
        average //= processed

    return {
        "found": found,
        "processed": processed,
        "average": average
        }


def register_superjob(key):
    url = "https://api.superjob.ru/2.0/oauth2/password/"
    payload = {
        "login": os.environ.get('LOGIN'),
        "password": os.environ.get('PASSWORD'),
        "client_id": int(os.environ.get('CLIENT_ID')),
        "client_secret": key
    }
    response = requests.get(url, params=payload)
    response.raise_for_status()
    return response.json()["access_token"]


def get_language_stats_sj(language, key):
    found = 0
    processed = 0
    average = 0

    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {
        "X-Api-App-Id": key,
        "Authorization": f"Bearer {register_superjob(key)}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    for page in count(0):
        payload = {
            "keyword": f'Программист {language}',
            "town": 4,
            "page": page,
            "count": 100
        }
        response = requests.get(url, headers=headers, params=payload)
        response.raise_for_status()

        res_json = response.json()
        for vacancy in res_json["objects"]:
            salary = predict_rub_salary_sj(vacancy)
            if salary:
                average += salary
                processed += 1

        found += res_json["total"]

        if not res_json['more']:
                break

    if processed:
        average //= processed

    return {
        "found": found,
        "processed": processed,
        "average": average
        }


def return_beautiful_table(statistics, title):
    table_data = [
        (
            "Язык программирования",
            "Вакансий найдено",
            "Вакансий обработано",
            "Средняя зарплата"
        )
    ]
    for language in statistics:
        info = statistics[language]
        table_data.append(
            (
                language,
                info["found"],
                info["processed"],
                info["average"]
            )
        )

    table_instance = AsciiTable(table_data, title)
    table_instance.justify_columns[2] = 'right'
    return table_instance.table


if __name__ == "__main__":
    load_dotenv()
    sj_key = os.environ.get('KEY')
    
    count_of_language = {
        "Python": {},
        "Java": {},
        "C++": {},
        "C#": {},
        "Rust": {},
        "Ruby": {},
        "1C": {}
    }

    for language in count_of_language:
        try:
            count_of_language[language] = get_language_stats_hh(language)
        except RuntimeError:
            count_of_language[language] = {
                "found": 0,
                "processed": 0,
                "average": 0
            }
    print(
        return_beautiful_table(
            count_of_language,
            "HeadHunter Moscow"
        ),
        end="\n\n"
    )

    for language in count_of_language:
        try:
            count_of_language[language] = get_language_stats_sj(language, sj_key)
        except RuntimeError:
            count_of_language[language] = {
                "found": 0,
                "processed": 0,
                "average": 0
            }
    print(
        return_beautiful_table(
            count_of_language,
            "SuperJob Moscow"
    ))
