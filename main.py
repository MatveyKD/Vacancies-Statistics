import os
from itertools import count

import requests
from terminaltables import AsciiTable
from dotenv import load_dotenv


load_dotenv()



def predict_salary(from_salary, to_salary):
    if from_salary:
        if to_salary:
            return (from_salary + to_salary) / 2
        else:
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
    count_of_lenguage = {
        "Python": {},
        "Java": {},
        "C++": {},
        "C#": {},
        "Rust": {},
        "Assembly": {},
        "1C": {}
    }

    url = "https://api.hh.ru/vacancies"

    for lenguage in count_of_lenguage:
        count_of_lenguage[lenguage]["average"] = 0
        count_of_lenguage[lenguage]["processed"] = 0

        for page in count(0):
            payload = {
                "text": f"Программист {lenguage}",
                "area": 1,
                "page": page,
                "per_page": 100
            }

            r = requests.get(url, params=payload)
            r.raise_for_status()
            for vac in r.json()["items"]:
                salary = predict_rub_salary_hh(vac)
                if salary:
                    count_of_lenguage[lenguage]["average"] += salary
                    count_of_lenguage[lenguage]["processed"] += 1
            count_of_lenguage[lenguage]["found"] = r.json()["found"]

            if page >= r.json()['pages'] - 1:
                break

        count_of_lenguage[lenguage]["average"] = count_of_lenguage[lenguage][
            "average"] // count_of_lenguage[lenguage]["processed"]

    return count_of_lenguage


def register_superjob():
    key = os.environ.get('KEY')
    url = "https://api.superjob.ru/2.0/oauth2/password/"
    payload = {
        "login": os.environ.get('LOGIN'),
        "password": os.environ.get('PASSWORD'),
        "client_id": int(os.environ.get('CLIENT_ID')),
        "client_secret": key
    }
    r = requests.get(url, params=payload)
    r.raise_for_status()
    return r.json()["access_token"]


def get_vacancies_superjob():
    count_of_lenguage = {
        "Python": {},
        "Java": {},
        "JS": {},
        "C++": {},
        "C#": {},
        "PHP": {},
        "1C": {}
    }
    
    key = os.environ.get('KEY')
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {
        "X-Api-App-Id": key,
        "Authorization": f"Bearer {register_superjob()}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    for lenguage in count_of_lenguage:
        count_of_lenguage[lenguage]["average"] = 0
        count_of_lenguage[lenguage]["processed"] = 0
        count_of_lenguage[lenguage]["found"] = 0
        for page in count(0):
            payload = {
                "keyword": f'Программист {lenguage}',
                "town": 4,
                "page": page,
                "count": 100
            }
            r = requests.get(url, headers=headers, params=payload)
            r.raise_for_status()
            #print(r.json())
            for vacancy in r.json()["objects"]:
                #print(vacancy["profession"] + ", Москва, " + str(predict_rub_salary_sj(vacancy)))
                salary = predict_rub_salary_sj(vacancy)
                if salary:
                    count_of_lenguage[lenguage]["average"] += salary
                    count_of_lenguage[lenguage]["processed"] += 1
                    count_of_lenguage[lenguage]["found"] += r.json()["total"]
    
            if not r.json()['more']:
                    break
        count_of_lenguage[lenguage]["average"] //= count_of_lenguage[lenguage]["processed"]
    return count_of_lenguage

def beautiful_print(statistics, title):
    table_data = [
        (
            "Язык программирования",
            "Вакансий найдено",
            "Вакансий обработано",
            "Средняя зарплата"
        )
    ]
    for lenguage in statistics:
        info = statistics[lenguage]
        table_data.append(
            (
                lenguage,
                info["found"],
                info["processed"],
                info["average"]
            )
        )

    table_instance = AsciiTable(table_data, title)
    table_instance.justify_columns[2] = 'right'
    return table_instance.table
    

if __name__ == "__main__":
    print(
        beautiful_print(
            get_vacancies_hhru(),
            "HeadHunter Moscow"
        ),
        end="\n\n"
    )
    print(beautiful_print(
        get_vacancies_superjob(),
        "SuperJob Moscow"
    ))
