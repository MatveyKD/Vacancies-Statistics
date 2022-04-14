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
    return None


def predict_rub_salary_hh(vacancy):
    if vacancy["salary"]:
        from_salary = vacancy["salary"]["from"]
        to_salary = vacancy["salary"]["to"]
        valute = vacancy["salary"]["currency"]
        if valute == "RUR":
            return predict_salary(from_salary, to_salary)
    return None


def predict_rub_salary_sj(vacancy):
    payment_from = vacancy["payment_from"]
    payment_to = vacancy["payment_to"]
    valute = vacancy["currency"]
    if valute == "rub":
        return predict_salary(payment_from, payment_to)
    return None


def get_vacancies_hhru():
    count_of_language = {
        "Python": {},
        "Java": {},
        "C++": {},
        "C#": {},
        "Rust": {},
        "Assembly": {},
        "1C": {}
    }

    url = "https://api.hh.ru/vacancies"

    for language in count_of_language:
        count_of_language[language]["average"] = 0
        count_of_language[language]["processed"] = 0

        for page in count(0):
            payload = {
                "text": f"Программист {language}",
                "area": 1,
                "page": page,
                "per_page": 100
            }

            response = requests.get(url, params=payload)
            try:
                response.raise_for_status()
            except:
                count_of_language[language]["average"] = 0
                count_of_language[language]["processed"] = 0
                count_of_language[language]["found"] = 0
                break
                
            res_json = response.json()
            for vacancy in res_json["items"]:
                salary = predict_rub_salary_hh(vacancy)
                if salary:
                    count_of_language[language]["average"] += salary
                    count_of_language[language]["processed"] += 1
            count_of_language[language]["found"] = res_json["found"]

            if page >= res_json['pages'] - 1:
                break

        if count_of_language[language]["processed"] != 0:
            count_of_language[language]["average"] = count_of_language[language][
                "average"] // count_of_language[language]["processed"]

    return count_of_language


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


def get_vacancies_superjob(key):
    count_of_language = {
        "Python": {},
        "Java": {},
        "JS": {},
        "C++": {},
        "C#": {},
        "PHP": {},
        "1C": {}
    }

    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {
        "X-Api-App-Id": key,
        "Authorization": f"Bearer {register_superjob(key)}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    for language in count_of_language:
        count_of_language[language]["average"] = 0
        count_of_language[language]["processed"] = 0
        count_of_language[language]["found"] = 0
        for page in count(0):
            payload = {
                "keyword": f'Программист {language}',
                "town": 4,
                "page": page,
                "count": 100
            }
            response = requests.get(url, headers=headers, params=payload)
            try:
                response.raise_for_status()
            except:
                count_of_language[language]["average"] = 0
                count_of_language[language]["processed"] = 0
                count_of_language[language]["found"] = 0
                break

            res_json = response.json()
            for vacancy in res_json["objects"]:
                salary = predict_rub_salary_sj(vacancy)
                if salary:
                    count_of_language[language]["average"] += salary
                    count_of_language[language]["processed"] += 1
                    count_of_language[language]["found"] += res_json["total"]

            if not res_json['more']:
                    break
        if count_of_language[language]["processed"] != 0:
            count_of_language[language]["average"] //= count_of_language[language]["processed"]
    return count_of_language


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
    print(
        return_beautiful_table(
            get_vacancies_hhru(),
            "HeadHunter Moscow"
        ),
        end="\n\n"
    )
    print(
        return_beautiful_table(
            get_vacancies_superjob(sj_key),
            "SuperJob Moscow"
    ))
