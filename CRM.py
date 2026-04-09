import os
import uuid
import json
from datetime import datetime, timedelta
from flask import Flask, session, request, render_template_string, redirect, url_for, jsonify

app = Flask(__name__)
app.secret_key = 'super_secret_key_control365'

# ==========================================
# БАЗА ДАННЫХ И СЛОВАРИ (Бэкенд)
# ==========================================

WORKERS_DB = ['Стас', 'Иван', 'Игорь', 'Матвей', 'Наиль']

STOCK_DB = [
    {'id': 'st1', 'name': 'Замена вентиля металлического', 'price': 300},
    {'id': 'st2', 'name': 'Груза набивные для стальных дисков', 'price': 0},
    {'id': 'st3', 'name': 'Заправка фреоном R134', 'price': 2},
    {'id': 'st4', 'name': 'Вентиль обычный TR-414', 'price': 50},
    {'id': 'st5', 'name': 'Герметик борта (порция)', 'price': 200},
    {'id': 'st6', 'name': 'Пакет для шин (1 шт)', 'price': 30}
]
STOCK_MAP = {item['id']: item['name'] for item in STOCK_DB}

SRV_NAMES = {
    'car': { 'srv1':'Снятие и установка', 'srv2':'Балансировка', 'srv3':'Снятие | Установка | Балансировка', 'srv4':'Комплекс 1* колеса', 'srv5':'Комплекс 4* колеса', 'srv6':'Правка дисков', 'srv7':'Монтаж', 'srv8':'Демонтаж', 'srv9':'Демонтаж и монтаж', 'srv10':'Покраска дисков' },
    'truck': { 'tr1':'Снятие/Установка (Вед)', 'tr2':'Снятие/Установка (Рул)', 'tr3':'Балансировка', 'tr4':'С/У/Баланс (Вед)', 'tr5':'С/У/Баланс (Рул)', 'tr6':'Комплекс 1* (Вед)', 'tr7':'Комплекс 1* (Рул)', 'tr8':'Монтаж', 'tr9':'Демонтаж', 'tr10':'Демонтаж и монтаж', 'tr11':'Нарезка протектора' }
}

PRICES_DB = {'car': {}, 'jeep': {}, 'truck': {}}
radii = ['R13', 'R14', 'R15', 'R16', 'R17', 'R18', 'R19', 'R20', 'R21', 'R22']
base_car = {'srv1': 150, 'srv2': 200, 'srv3': 300, 'srv4': 400, 'srv5': 1500, 'srv6': 2000, 'srv7': 150, 'srv8': 150, 'srv9': 250, 'srv10': 1200}

for r in radii:
    r_num = int(r[1:])
    multiplier = 1.0 + (r_num - 13) * 0.1  
    PRICES_DB['car'][r] = {k: int(v * multiplier) for k, v in base_car.items()}
    PRICES_DB['jeep'][r] = {k: int(v * multiplier * 1.3) for k, v in base_car.items()}

PRICES_DB['truck']['default'] = {
    'tr1': 500, 'tr2': 500, 'tr3': 700, 'tr4': 1200, 'tr5': 1200, 'tr6': 1500, 'tr7': 1500, 'tr8': 400, 'tr9': 400, 'tr10': 700, 'tr11': 1000
}

today_str = datetime.now().strftime('%d.%m.%y')
yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%d.%m.%y')

ORDERS_DB = {
    'in_work': [
        {'id': '8', 'date': f'{today_str} 11:00', 'type': 'Легковые', 'type_id': 'car', 'radius': 'R15', 'num': 'М123ММ', 'mark': 'BMW', 'phone': '+7(999)-111-22-33', 'name': 'Алексей', 'master': 'Стас', 'amount': '1500', 'discount': 0, 'payment_method': 'Наличные', 'status': 'in_work', 'services': {'srv3': 1}, 'stock': {}},
        {'id': '9', 'date': f'{yesterday_str} 18:30', 'type': 'Внедорожники', 'type_id': 'jeep', 'radius': 'R19', 'num': 'А999АА', 'mark': 'Toyota', 'phone': '+7(900)-000-00-00', 'name': 'Михаил', 'master': 'Наиль', 'amount': '4500', 'discount': 0, 'payment_method': 'Счёт', 'status': 'in_work', 'services': {'srv5': 1}, 'stock': {}}
    ],
    'closed': [
        {'id': '1', 'date': '01.03.26 10:33', 'type': 'Легковые', 'type_id': 'car', 'radius': 'R17', 'num': 'БН', 'mark': '', 'phone': '+7(913)-147-98-34', 'name': 'Клиент 1', 'master': 'Игорь', 'amount': '400', 'discount': 0, 'payment_method': 'Наличные', 'status': 'closed', 'services': {'srv1': 1}, 'stock': {}},
        {'id': '2', 'date': '01.03.26 13:36', 'type': 'Легковые', 'type_id': 'car', 'radius': 'R14', 'num': 'БН', 'mark': 'Kia', 'phone': '+7(913)-147-98-34', 'name': 'Клиент 1', 'master': 'Игорь', 'amount': '2150', 'discount': 0, 'payment_method': 'Карта', 'status': 'closed', 'services': {'srv4': 1}, 'stock': {}},
        {'id': '3', 'date': '01.03.26 15:23', 'type': 'Легковые', 'type_id': 'car', 'radius': 'R15', 'num': 'БН', 'mark': '', 'phone': '+7(913)-147-98-34', 'name': 'Клиент 1', 'master': 'Игорь', 'amount': '290', 'discount': 0, 'payment_method': 'Карта', 'status': 'closed', 'services': {'srv1': 1}, 'stock': {}},
        {'id': '4', 'date': '01.03.26 17:59', 'type': 'Легковые', 'type_id': 'car', 'radius': 'R15', 'num': 'БН', 'mark': 'Mercedes', 'phone': '+7(913)-147-98-34', 'name': 'Клиент 1', 'master': 'Игорь', 'amount': '4110', 'discount': 0, 'payment_method': 'Карта', 'status': 'closed', 'services': {'srv9': 1, 'srv6': 1, 'srv3': 4}, 'stock': {}},
        {'id': '5', 'date': '01.03.26 19:24', 'type': 'Легковые', 'type_id': 'car', 'radius': 'R14', 'num': 'БН', 'mark': '', 'phone': '+7(999)-111-22-33', 'name': 'Алексей', 'master': 'Игорь', 'amount': '300', 'discount': 0, 'payment_method': 'Наличные', 'status': 'closed', 'services': {'srv1': 1}, 'stock': {}},
        {'id': '6', 'date': '02.03.26 09:07', 'type': 'Легковые', 'type_id': 'car', 'radius': 'R14', 'num': 'В777ВВ', 'mark': 'Honda', 'phone': '+7(922)-222-22-22', 'name': 'Дмитрий', 'master': 'Игорь', 'amount': '1050', 'discount': 10, 'payment_method': 'Наличные', 'status': 'closed', 'services': {'srv4': 1}, 'stock': {}},
        {'id': '7', 'date': '02.03.26 10:49', 'type': 'Легковые', 'type_id': 'car', 'radius': 'R16', 'num': 'БН', 'mark': 'Lada', 'phone': '+7(900)-000-00-00', 'name': 'Михаил', 'master': 'Игорь', 'amount': '3460', 'discount': 0, 'payment_method': 'Карта', 'status': 'closed', 'services': {'srv9': 1, 'srv6': 1}, 'stock': {}}
    ]
}

# БД РАСХОДОВ
EXPENSES_DB = [
    {'id': 'e1', 'date': '31.03.26', 'desc': 'Налог', 'payment': 'Наличные', 'deduct': True, 'amount': 12200},
    {'id': 'e2', 'date': '27.03.26', 'desc': 'Шланг воздушный 2 штуки', 'payment': 'Наличные', 'deduct': True, 'amount': 3000},
    {'id': 'e3', 'date': '27.03.26', 'desc': 'Термоклей', 'payment': 'Наличные', 'deduct': True, 'amount': 1000},
    {'id': 'e4', 'date': '27.03.26', 'desc': 'Чернитель 6 литров', 'payment': 'Наличные', 'deduct': True, 'amount': 1650},
    {'id': 'e5', 'date': '27.03.26', 'desc': 'Интернет', 'payment': 'Наличные', 'deduct': True, 'amount': 1600},
    {'id': 'e6', 'date': '27.03.26', 'desc': 'Yclients', 'payment': 'Наличные', 'deduct': True, 'amount': 8000},
    {'id': 'e7', 'date': '27.03.26', 'desc': 'CRM', 'payment': 'Наличные', 'deduct': True, 'amount': 36000},
    {'id': 'e8', 'date': '27.03.26', 'desc': 'Реклама 2гис', 'payment': 'Наличные', 'deduct': True, 'amount': 96000}
]

def get_kassa_totals():
    cash = 0
    card = 0
    invoice = 0
    
    # Доходы (закрытые заказы)
    for o in ORDERS_DB['closed']:
        amt = int(str(o.get('amount', '0')).replace(' ₽', '').replace(' ', ''))
        pay = o.get('payment_method', 'Наличные')
        if pay == 'Наличные': cash += amt
        elif pay in ['Карта', 'СБП', 'Перевод']: card += amt
        elif pay == 'Счёт': invoice += amt
            
    # Расходы
    for e in EXPENSES_DB:
        if e.get('deduct', False):
            pay = e.get('payment', 'Наличные')
            amt = e.get('amount', 0)
            if pay == 'Наличные': cash -= amt
            elif pay == 'Счёт': invoice -= amt
            
    return {
        'cash': f"{cash:,} ₽".replace(',', ' '),
        'card': f"{card:,} ₽".replace(',', ' '),
        'invoice': f"{invoice:,} ₽".replace(',', ' ')
    }

# ==========================================
# ШАБЛОНЫ HTML И CSS
# ==========================================

LOGIN_HTML = """
<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><title>Вход</title>
<style>
    body { font-family: sans-serif; background: #e0e0e0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    .login-card { background: white; padding: 40px; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 320px; text-align: center; border-top: 5px solid #00b300; }
    input { width: 100%; padding: 12px; border: 1px solid #ccc; margin-bottom: 15px; box-sizing: border-box; }
    button { width: 100%; padding: 12px; background: #00b300; color: white; border: none; font-weight: bold; cursor: pointer; }
</style></head><body>
    <div class="login-card"><h2>CONTROL365</h2>
        <form method="POST"><input type="text" name="phone" value="+7 (932)-322-22-12"><input type="password" name="password" value="admin"><button type="submit">Войти</button></form>
    </div>
</body></html>
"""

BASE_HTML = """
<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><title>CONTROL365</title>
<script type="text/javascript" src="https://cdn.jsdelivr.net/jquery/latest/jquery.min.js"></script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/momentjs/latest/moment.min.js"></script>
<script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.4/locale/ru.min.js"></script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/daterangepicker/daterangepicker.min.js"></script>
<link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/daterangepicker/daterangepicker.css" />

<style>
    body { margin: 0; font-family: Arial, sans-serif; background: #f4f5f8; display: flex; flex-direction: column; height: 100vh; overflow: hidden; color: #333; }
    .topbar { display: flex; border-bottom: 1px solid #ddd; background: #fff; height: 50px; flex-shrink: 0; z-index: 50; }
    .tab-link { display: flex; align-items: center; padding: 0 20px; text-decoration: none; color: #555; border-right: 1px solid #eee; cursor: pointer; font-size: 14px; }
    .tab-link.active { font-weight: bold; color: #000; box-shadow: inset 0 -3px 0 #000; }
    .badge { color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-left: 8px; }
    .bg-orange { background: #ff7f00; } .bg-green { background: #00b300; }
    .dropdown { position: relative; display: flex; }
    .dropdown-menu { display: none; position: absolute; top: 50px; left: 0; background: white; border: 1px solid #ccc; box-shadow: 0 4px 8px rgba(0,0,0,0.1); min-width: 200px; z-index: 100; flex-direction: column; }
    .dropdown-menu.show { display: flex; }
    .dropdown-menu a { padding: 12px 15px; text-decoration: none; color: #333; border-bottom: 1px solid #f0f0f0; }
    .dropdown-menu a:hover { background: #f9f9f9; }
    .burger-menu { margin-left: auto; padding: 0 20px; display: flex; align-items: center; font-size: 20px; cursor: pointer; border-left: 1px solid #eee; }
    .burger-menu:hover { background: #f9f9f9; }

    .sidebar { position: fixed; top: 0; right: -280px; width: 280px; height: 100vh; background: #ffffff; color: #333; transition: 0.3s; z-index: 1000; display: flex; flex-direction: column; box-shadow: -5px 0 15px rgba(0,0,0,0.1);}
    .sidebar.open { right: 0; }
    .sidebar-header { padding: 20px; color: #888; font-size: 15px; border-bottom: 1px solid #eee; margin-bottom: 5px; font-family: monospace;}
    .sidebar a { padding: 12px 20px; color: #333; text-decoration: none; display: block; font-size: 15px; transition: background 0.2s;}
    .sidebar a:hover { background: #f9f9f9; }
    .sidebar a.active { background: #f4f5f8; font-weight: bold; color: #000; border-left: 4px solid #333; padding-left: 16px;}
    .overlay { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.4); z-index: 999; }
    .overlay.show { display: block; }
    .main-container { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: #f4f5f8; position: relative; }
</style></head><body>

    {% if show_topbar %}
    <div class="topbar">
        <a href="/checkout?status=in_work" class="tab-link {{ 'active' if current_status == 'in_work' else '' }}">В работе <span class="badge bg-orange">{{ in_work_count }}</span></a>
        <a href="/checkout?status=closed" class="tab-link {{ 'active' if current_status == 'closed' else '' }}">Закрытые <span class="badge bg-green">{{ closed_count }}</span></a>
        <div class="dropdown">
            <div class="tab-link" onclick="document.getElementById('kassaMenu').classList.toggle('show'); event.stopPropagation();">Касса ▾</div>
            <div class="dropdown-menu" id="kassaMenu">
                <a href="#">💵 {{ kassa.cash }}</a><a href="#">💳 {{ kassa.card }}</a><a href="#">🧾 {{ kassa.invoice }}</a>
                <a href="#">Открыть смену</a><a href="#">Х-отчет</a><a href="#">Закрыть смену</a>
            </div>
        </div>
        <div class="burger-menu" onclick="toggleSidebar()">☰</div>
    </div>
    {% else %}
    <div class="topbar" style="justify-content: flex-end;">
        <div class="burger-menu" onclick="toggleSidebar()" style="border-left: none;">☰</div>
    </div>
    {% endif %}
    
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">79323222212</div>
        <a href="/dashboard" class="{{ 'active' if current_tab == 'dashboard' else '' }}">Панель управления</a>
        <a href="/checkout?status=in_work" class="{{ 'active' if current_tab == 'checkout' else '' }}">Оформление заказов</a>
        <a href="/orders_list" class="{{ 'active' if current_tab == 'orders_list' else '' }}">Заказы</a>
        <a href="/clients" class="{{ 'active' if current_tab == 'clients' else '' }}">Клиенты</a>
        <a href="/expenses" class="{{ 'active' if current_tab == 'expenses' else '' }}">Расходы</a>
        <a href="#">Отчёты</a><a href="#">Зарплаты</a><a href="#">Склад</a>
        <a href="#">Настройки</a><a href="#">Баланс</a>
        <a href="/logout" style="margin-top: auto; border-top: 1px solid #eee;">Выход</a>
    </div>
    <div class="overlay" id="overlay" onclick="toggleSidebar()"></div>
    <div class="main-container">{{ content | safe }}</div>
    
    <script>
        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('open');
            document.getElementById('overlay').classList.toggle('show');
        }
        document.addEventListener('click', function(e) {
            const menu = document.getElementById('kassaMenu');
            if (menu && menu.classList.contains('show') && !e.target.closest('.dropdown')) { menu.classList.remove('show'); }
        });
    </script>
</body></html>
"""

# ВКЛАДКА РАСХОДЫ
EXPENSES_HTML = """
<style>
    .exp-container { flex: 1; padding: 20px; background: #fff; display: flex; flex-direction: column; overflow: hidden; }
    .exp-header { display: flex; gap: 10px; margin-bottom: 20px; align-items: center; }
    
    .date-input-wrapper { position: relative; display: inline-block; }
    .date-input-wrapper input { padding: 9px 30px 9px 12px; border: 1px solid #ccc; border-radius: 4px; outline: none; background: #fff; width: 170px; cursor: pointer; }
    .date-input-wrapper::after { content: '📅'; position: absolute; right: 10px; top: 50%; transform: translateY(-50%); pointer-events: none; font-size: 14px; }
    
    .btn-primary { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold; transition: 0.2s;}
    .btn-primary:hover { background: #0056b3; }
    .btn-success { background: #00b300; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold; transition: 0.2s;}
    .btn-success:hover { background: #009900; }
    
    .table-wrapper { flex: 1; overflow: auto; border: 1px solid #eee; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; white-space: nowrap; }
    th, td { padding: 15px; text-align: left; border-bottom: 1px solid #eee;}
    th { background: #fbfbfb; font-weight: bold; position: sticky; top: 0; z-index: 10; box-shadow: 0 2px 2px -1px rgba(0,0,0,0.1);}
    
    .cash-icon { display: inline-block; background: #ffc107; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-left: 10px;}
    .btn-del { background: #fff; border: 1px solid #ffcccc; color: #d9534f; border-radius: 4px; width: 30px; height: 30px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 16px; transition: 0.2s;}
    .btn-del:hover { background: #ffe6e6; }
    
    /* Модалка расходов */
    .modal-overlay { display: none; position: fixed; top:0; left:0; right:0; bottom:0; background: rgba(0,0,0,0.5); z-index: 2000; align-items: center; justify-content: center; }
    .modal-content { background: #fff; padding: 25px; width: 400px; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
    .modal-content h3 { margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 20px; }
    
    .form-group { margin-bottom: 15px; }
    .form-group label { display: block; font-weight: bold; margin-bottom: 5px; font-size: 14px; color: #333;}
    .form-group input[type="text"], .form-group input[type="number"] { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; outline: none;}
    
    .pay-toggle { display: flex; border-radius: 4px; overflow: hidden; border: 1px solid #ccc;}
    .pt-btn { flex: 1; text-align: center; padding: 10px; cursor: pointer; background: #eee; font-weight: bold; color: #555; transition: 0.2s;}
    .pt-btn.active { background: #00b300; color: white; border-color: #00b300;}
    
    .modal-footer { display: flex; gap: 10px; margin-top: 25px; border-top: 1px solid #eee; padding-top: 15px;}
    .btn-cancel { background: #e0e0e0; color: #333; border: none; padding: 12px; font-weight: bold; border-radius: 4px; cursor: pointer; flex: 1; }
    .btn-create-exp { background: #88d49e; color: white; border: none; padding: 12px; font-weight: bold; border-radius: 4px; cursor: pointer; flex: 1; }
    .btn-create-exp.ready { background: #00b300; }
</style>

<div class="exp-container">
    <div class="exp-header">
        <div class="date-input-wrapper">
            <input type="text" id="expDateRange">
        </div>
        <button class="btn-primary" onclick="filterExpenses()">Отчет</button>
        <button class="btn-success" onclick="openExpModal()">Создать расход</button>
    </div>

    <div class="table-wrapper">
        <table>
            <thead>
                <tr><th>Дата</th><th>Комментарий</th><th>Оплата</th><th style="text-align:right;">Сумма</th><th style="width:50px; text-align:center;">📄</th></tr>
            </thead>
            <tbody>
                {% if expenses %}
                    {% for e in expenses %}
                    <tr id="exp-row-{{ e.id }}">
                        <td style="color:#666;">{{ e.date }}</td>
                        <td>{{ e.desc }}</td>
                        <td>{{ e.payment }} {% if e.payment == 'Наличные' and e.deduct %}<span class="cash-icon">⏏</span>{% endif %}</td>
                        <td style="text-align:right; font-weight:bold;">{{ e.amount }} ₽</td>
                        <td style="text-align:center;"><button class="btn-del" onclick="deleteExpense('{{ e.id }}')" title="Удалить">🗑️</button></td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr><td colspan="5" style="text-align:center; padding: 50px; color: #888;">Расходов в выбранном периоде нет</td></tr>
                {% endif %}
            </tbody>
        </table>
    </div>
</div>

<div class="modal-overlay" id="expModal">
    <div class="modal-content">
        <h3>Создание расхода</h3>
        
        <div class="form-group">
            <label>Дата</label>
            <div class="date-input-wrapper" style="width: 100%;">
                <input type="text" id="newExpDate" style="width: 100%;">
            </div>
        </div>
        
        <div class="form-group">
            <label>Описание</label>
            <input type="text" id="newExpDesc">
        </div>
        
        <div class="form-group">
            <label>Оплата</label>
            <div class="pay-toggle">
                <div class="pt-btn active" onclick="setExpPay(this, 'Наличные')">Наличные</div>
                <div class="pt-btn" onclick="setExpPay(this, 'Счёт')">Счёт</div>
            </div>
        </div>
        
        <div class="form-group">
            <label style="display: flex; align-items: center; gap: 8px; font-weight: normal; cursor: pointer;">
                <input type="checkbox" id="newExpDeduct" checked style="width: 16px; height: 16px;"> Списать из кассы
            </label>
        </div>
        
        <div class="form-group">
            <label>Сумма</label>
            <input type="number" id="newExpAmount" oninput="checkExpForm()">
        </div>
        
        <div class="modal-footer">
            <button class="btn-cancel" onclick="closeExpModal()">Отмена</button>
            <button class="btn-create-exp" id="btnSubmitExp" onclick="saveExpense()" disabled>Создать</button>
        </div>
    </div>
</div>

<script>
    let currentExpPay = 'Наличные';

    $(function() {
        $('#expDateRange').daterangepicker({
            opens: 'right', locale: { format: 'DD.MM.YY', applyLabel: 'Применить', cancelLabel: 'Отмена', customRangeLabel: 'Другой', daysOfWeek: ['Вс','Пн','Вт','Ср','Чт','Пт','Сб'], monthNames: ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'], firstDay: 1 },
            ranges: { 
               'Сегодня': [moment(), moment()], 
               'Вчера': [moment().subtract(1, 'days'), moment().subtract(1, 'days')], 
               'Последние 7 дней': [moment().subtract(6, 'days'), moment()], 
               'Последние 30 дней': [moment().subtract(29, 'days'), moment()], 
               'Этот месяц': [moment().startOf('month'), moment().endOf('month')], 
               'Прошлый месяц': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')] 
            },
            startDate: moment('2026-03-01'), endDate: moment('2026-03-31')
        });

        $('#newExpDate').daterangepicker({
            singleDatePicker: true, showDropdowns: true,
            locale: { format: 'DD.MM.YY', daysOfWeek: ['Вс','Пн','Вт','Ср','Чт','Пт','Сб'], monthNames: ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'], firstDay: 1 }
        });

        {% if selected_dates %}
            $('#expDateRange').val("{{ selected_dates }}");
            let dates = "{{ selected_dates }}".split('-');
            if (dates.length === 2) {
                $('#expDateRange').data('daterangepicker').setStartDate(dates[0].trim());
                $('#expDateRange').data('daterangepicker').setEndDate(dates[1].trim());
            }
        {% endif %}
    });

    function filterExpenses() {
        const dateStr = document.getElementById('expDateRange').value;
        window.location.href = '/expenses?dates=' + encodeURIComponent(dateStr);
    }

    function openExpModal() {
        document.getElementById('newExpDesc').value = '';
        document.getElementById('newExpAmount').value = '';
        document.getElementById('newExpDeduct').checked = true;
        setExpPay(document.querySelector('.pt-btn'), 'Наличные');
        checkExpForm();
        document.getElementById('expModal').style.display = 'flex';
    }

    function closeExpModal() {
        document.getElementById('expModal').style.display = 'none';
    }

    function setExpPay(el, val) {
        document.querySelectorAll('.pt-btn').forEach(b => b.classList.remove('active'));
        el.classList.add('active');
        currentExpPay = val;
    }

    function checkExpForm() {
        let amt = document.getElementById('newExpAmount').value;
        let btn = document.getElementById('btnSubmitExp');
        if(amt && parseInt(amt) > 0) {
            btn.classList.add('ready');
            btn.disabled = false;
        } else {
            btn.classList.remove('ready');
            btn.disabled = true;
        }
    }

    function saveExpense() {
        let payload = {
            date: document.getElementById('newExpDate').value,
            desc: document.getElementById('newExpDesc').value,
            payment: currentExpPay,
            deduct: document.getElementById('newExpDeduct').checked,
            amount: document.getElementById('newExpAmount').value
        };

        fetch('/api/save_expense', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
        }).then(res => res.json()).then(data => {
            if(data.status === 'success') window.location.reload();
        });
    }

    function deleteExpense(id) {
        if(confirm('Удалить этот расход? (Сумма вернется в кассу)')) {
            fetch('/api/delete_expense', {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({id: id})
            }).then(res => res.json()).then(data => {
                if(data.status === 'success') window.location.reload();
            });
        }
    }
</script>
"""
CHECKOUT_LIST_HTML = """
<style>
    .table-wrapper { flex: 1; overflow-y: auto; padding-bottom: 20px; background: #fff;}
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { padding: 12px 20px; text-align: left; border-bottom: 1px solid #eee; }
    .btn-create-container { padding: 10px; background: white; border-top: 1px solid #eee; }
    .btn-create { display: block; background: #00b300; color: white; text-align: center; padding: 15px 0; text-decoration: none; font-weight: bold; border-radius: 4px; font-size: 16px;}
    .clickable-row { transition: background 0.2s; cursor: pointer; }
    .clickable-row:hover { background-color: #eafbee; }
</style>
<div class="table-wrapper">
    {% if orders %}
        <table><tbody>
            {% for o in orders %}
            <tr class="clickable-row" onclick="window.location.href='/create_order?id={{ o.id }}'">
                <td style="color:#666; width: 120px;">{{ o.raw_date }}</td>
                <td>({{ o.type }}) {{ o.num }}</td>
                <td>{{ o.master }}</td>
                <td style="font-weight:bold; text-align: right; color: #00b300;">{{ o.amount }} ₽</td>
            </tr>
            {% endfor %}
        </tbody></table>
    {% else %}
        <div style="text-align:center; padding: 50px; color: #888;">За последние 2 дня заказов нет</div>
    {% endif %}
</div>
<div class="btn-create-container"><a href="/create_order" class="btn-create">СОЗДАТЬ ЗАКАЗ</a></div>
"""

CLIENTS_HTML = """
<style>
    .clients-container { flex: 1; padding: 20px; background: #fff; display: flex; flex-direction: column; overflow: hidden; }
    .client-search-bar { display: flex; gap: 10px; margin-bottom: 20px; align-items: center; }
    .client-search-bar input { padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px; outline: none; width: 200px; }
    .btn-search { background: #007bff; color: white; border: none; padding: 9px 20px; border-radius: 4px; cursor: pointer; font-weight: bold; transition: 0.2s;}
    .btn-search:hover { background: #0056b3; }
    .btn-show-all { background: #6c757d; color: white; border: none; padding: 9px 20px; border-radius: 4px; cursor: pointer; font-weight: bold; transition: 0.2s;}
    .btn-show-all:hover { background: #5a6268; }
    .btn-back { background: #e0e0e0; color: #333; border: none; padding: 6px 15px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 12px; margin-left: auto;}
    
    .table-wrapper { flex: 1; overflow: auto; border: 1px solid #eee; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; white-space: nowrap; }
    th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee;}
    th { background: #fbfbfb; font-weight: bold; position: sticky; top: 0; z-index: 10; box-shadow: 0 2px 2px -1px rgba(0,0,0,0.1);}
    
    .clickable-row { transition: background 0.2s; cursor: pointer; }
    .clickable-row:hover { background-color: #eafbee; }
    
    .history-header { display: flex; align-items: center; margin-bottom: 15px; background: #fbfbfb; padding: 10px 15px; border-radius: 4px; border: 1px solid #eee;}
</style>

<div class="clients-container">
    <div id="clientListContainer" style="display: flex; flex-direction: column; height: 100%;">
        <div class="client-search-bar">
            <input type="text" id="searchNum" placeholder="Номер авто (М123ММ)">
            <input type="text" id="searchPhone" placeholder="Телефон (+7...)">
            <button class="btn-search" onclick="searchClients()">Поиск</button>
            <button class="btn-show-all" onclick="showAllClients()">Показать всех</button>
        </div>

        <div class="table-wrapper">
            <table>
                <thead>
                    <tr><th>#</th><th>Телефон</th><th>Имя</th><th>Авто</th><th>Номер</th><th>Заказов</th><th>Сумма покупок</th></tr>
                </thead>
                <tbody id="clientsTableBody"></tbody>
            </table>
        </div>
    </div>

    <div id="clientHistoryContainer" style="display: none; flex-direction: column; height: 100%;">
        <div class="history-header">
            <h3 style="margin: 0;">История заказов: <span id="histTitle" style="color: #007bff;"></span></h3>
            <button class="btn-back" onclick="backToClients()">Назад к списку</button>
        </div>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr><th>#</th><th>Дата</th><th>Услуги</th><th>Работник</th><th>Оплата</th><th>Сумма</th></tr>
                </thead>
                <tbody id="historyTableBody"></tbody>
            </table>
        </div>
    </div>
</div>

<script>
    const CLIENTS_DATA = {{ clients | tojson | safe }};
    document.addEventListener("DOMContentLoaded", function() { renderClientsList(CLIENTS_DATA); });

    function renderClientsList(data) {
        let tbody = document.getElementById('clientsTableBody');
        let html = '';
        data.forEach((c, idx) => {
            html += `<tr class="clickable-row" onclick="showClientHistory('${c.phone}')">
                <td>${idx + 1}</td><td style="font-weight: bold;">${c.phone}</td><td>${c.name || '—'}</td>
                <td>${c.mark || '—'}</td><td>${c.num || '—'}</td><td>${c.orders.length} шт.</td>
                <td style="font-weight:bold; color:#00b300;">${c.total_amount.toLocaleString('ru-RU')} ₽</td>
            </tr>`;
        });
        if(data.length === 0) html = '<tr><td colspan="7" style="text-align:center; padding: 50px; color:#888;">Клиенты не найдены</td></tr>';
        tbody.innerHTML = html;
    }

    function searchClients() {
        let sNum = document.getElementById('searchNum').value.toLowerCase();
        let sPhone = document.getElementById('searchPhone').value.toLowerCase().replace(/\\D/g, ''); 
        
        let filtered = CLIENTS_DATA.filter(c => {
            let matchNum = c.num.toLowerCase().includes(sNum);
            let cleanPhone = c.phone.toLowerCase().replace(/\\D/g, '');
            let matchPhone = cleanPhone.includes(sPhone);
            return matchNum && matchPhone;
        });
        renderClientsList(filtered);
    }
    
    function showAllClients() {
        document.getElementById('searchNum').value = '';
        document.getElementById('searchPhone').value = '';
        renderClientsList(CLIENTS_DATA);
    }

    function showClientHistory(phone) {
        let client = CLIENTS_DATA.find(c => c.phone === phone);
        if(!client) return;
        document.getElementById('clientListContainer').style.display = 'none';
        document.getElementById('clientHistoryContainer').style.display = 'flex';
        document.getElementById('histTitle').innerText = `${client.phone} ${client.name ? '('+client.name+')' : ''}`;
        
        let tbody = document.getElementById('historyTableBody');
        let html = '';
        client.orders.forEach((o, idx) => {
            html += `<tr><td>${idx + 1}</td><td>${o.date}</td><td style="white-space: normal; line-height: 1.4;">${o.services}</td><td>${o.master}</td><td>${o.payment}</td><td style="font-weight:bold;">${o.amount}</td></tr>`;
        });
        tbody.innerHTML = html;
    }
    function backToClients() {
        document.getElementById('clientListContainer').style.display = 'flex';
        document.getElementById('clientHistoryContainer').style.display = 'none';
    }
</script>
"""

DASHBOARD_HTML = """
<style>
    .dash-container { padding: 20px; overflow-y: auto; height: 100%; box-sizing: border-box; }
    .dash-header { display: flex; gap: 10px; margin-bottom: 20px; align-items: center; }
    .dash-header select { padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px; outline: none; background: #fff; min-width: 150px; }
    .date-input-wrapper { position: relative; display: inline-block; }
    .date-input-wrapper input { padding: 8px 30px 8px 12px; border: 1px solid #ccc; border-radius: 4px; outline: none; background: #fff; width: 170px; cursor: pointer; }
    .date-input-wrapper::after { content: '📅'; position: absolute; right: 10px; top: 50%; transform: translateY(-50%); pointer-events: none; font-size: 14px; }
    .btn-primary { background: #007bff; color: white; border: none; padding: 9px 20px; border-radius: 4px; cursor: pointer; font-weight: bold; transition: 0.2s; font-size: 14px; }
    .btn-primary:hover { background: #0056b3; }
    .btn-primary:disabled { background: #99c2ff; cursor: not-allowed; }
    
    .dash-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .dash-card { background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); overflow: hidden; border: 1px solid #eaeaea; transition: opacity 0.3s;}
    
    .dash-table { width: 100%; border-collapse: collapse; font-size: 14px; }
    .dash-table th { background: #fbfbfb; padding: 12px 15px; text-align: left; font-weight: bold; border-bottom: 2px solid #eee; color: #333;}
    .dash-table td { padding: 12px 15px; border-bottom: 1px solid #eee; color: #555; }
    .dash-table tr:last-child td { border-bottom: none; }
    .dash-table td.num { text-align: right; }
    .dash-table tr.total td { font-weight: bold; color: #000; background: #fafafa; border-top: 2px solid #eee;}
</style>

<div class="dash-container">
    <div class="dash-header">
        <select id="workerFilter">
            <option value="(Все)">(Все работники)</option>
            {% for w in workers %}
                <option value="{{ w }}">{{ w }}</option>
            {% endfor %}
        </select>
        
        <div class="date-input-wrapper">
            <input type="text" id="reportDateRange">
        </div>
        
        <button id="reportBtn" class="btn-primary" onclick="generateReport()">Отчет</button>
    </div>

    <div class="dash-grid" id="reportDataArea">
        <div class="dash-card">
            <table class="dash-table">
                <thead><tr><th>Заказы</th><th class="num">Количество</th><th class="num">Сумма</th></tr></thead>
                <tbody>
                    <tr><td>Наличные</td><td class="num" id="d_cash_count">0</td><td class="num" id="d_cash">0 ₽</td></tr>
                    <tr><td>Счёт</td><td class="num" id="d_invoice_count">0</td><td class="num" id="d_invoice">0 ₽</td></tr>
                    <tr><td>Карта</td><td class="num" id="d_card_count">0</td><td class="num" id="d_card">0 ₽</td></tr>
                    <tr><td>Перевод</td><td class="num" id="d_transfer_count">0</td><td class="num" id="d_transfer">0 ₽</td></tr>
                    <tr class="total"><td>Итого</td><td class="num" id="d_total_orders_count">0</td><td class="num" id="d_total_orders">0 ₽</td></tr>
                </tbody>
            </table>
        </div>

        <div class="dash-card" style="align-self: start;">
            <table class="dash-table">
                <thead><tr><th>Параметры</th><th class="num">Значение</th></tr></thead>
                <tbody>
                    <tr><td>Средний чек</td><td class="num" id="d_avg_check">0.00 ₽</td></tr>
                    <tr><td>Загрузка объекта ❓</td><td class="num" id="d_obj_load">0,00 %</td></tr>
                    <tr><td>Загрузка работников ❓</td><td class="num" id="d_worker_load">0,00 %</td></tr>
                </tbody>
            </table>
        </div>

        <div class="dash-card" style="align-self: start;">
            <table class="dash-table">
                <thead><tr><th>Расходы</th><th class="num">Сумма</th></tr></thead>
                <tbody>
                    <tr><td>Зарплаты</td><td class="num" id="d_salary">0 ₽</td></tr>
                    <tr><td>Другое</td><td class="num" id="d_other_exp">0 ₽</td></tr>
                    <tr class="total"><td>Итого</td><td class="num" id="d_total_exp">0 ₽</td></tr>
                </tbody>
            </table>
        </div>

        <div class="dash-card">
            <table class="dash-table">
                <thead><tr><th>Скидки</th><th class="num">Количество</th><th class="num">Сумма</th></tr></thead>
                <tbody>
                    <tr><td>30%</td><td class="num" id="d_d30_count">0</td><td class="num" id="d_d30">0 ₽</td></tr>
                    <tr><td>20%</td><td class="num" id="d_d20_count">0</td><td class="num" id="d_d20">0 ₽</td></tr>
                    <tr><td>10%</td><td class="num" id="d_d10_count">0</td><td class="num" id="d_d10">0 ₽</td></tr>
                    <tr class="total"><td>Итого</td><td class="num" id="d_total_disc_count">0</td><td class="num" id="d_total_disc">0 ₽</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
    $(function() {
        $('#reportDateRange').daterangepicker({
            opens: 'right',
            locale: {
                format: 'DD.MM.YY', applyLabel: 'Применить', cancelLabel: 'Отмена', customRangeLabel: 'Другой',
                daysOfWeek: ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'], monthNames: ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'],
                firstDay: 1
            },
            ranges: {
               'Сегодня': [moment(), moment()],
               'Вчера': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
               'Последние 7 дней': [moment().subtract(6, 'days'), moment()],
               'Последние 30 дней': [moment().subtract(29, 'days'), moment()],
               'Этот месяц': [moment().startOf('month'), moment().endOf('month')],
               'Прошлый месяц': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
            },
            startDate: moment('2026-03-01'), 
            endDate: moment('2026-03-31')
        });
        generateReport();
    });

    function generateReport() {
        const btn = document.getElementById('reportBtn');
        const area = document.getElementById('reportDataArea');
        const dateStr = document.getElementById('reportDateRange').value;
        const workerStr = document.getElementById('workerFilter').value;
        
        let dates = dateStr.split('-');
        if(dates.length !== 2) return;

        btn.innerText = 'Загрузка...';
        btn.disabled = true;
        area.style.opacity = '0.4'; 
        
        fetch('/api/get_report', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ start: dates[0].trim(), end: dates[1].trim(), worker: workerStr })
        })
        .then(res => res.json()).then(data => {
            for (let key in data) {
                let el = document.getElementById('d_' + key);
                if(el) el.innerText = data[key];
            }
            btn.innerText = 'Отчет'; btn.disabled = false; area.style.opacity = '1';
        }).catch(err => {
            console.error(err); btn.innerText = 'Отчет'; btn.disabled = false; area.style.opacity = '1';
        });
    }
</script>
"""

ORDERS_FULL_TABLE_HTML = """
<style>
    .table-container { flex: 1; padding: 20px; background: #fff; display: flex; flex-direction: column; overflow: hidden; }
    .table-header-filters { display: flex; gap: 10px; margin-bottom: 15px; align-items: center; }
    .table-header-filters select { padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px; outline: none; background: #fff; }
    .date-input-wrapper { position: relative; display: inline-block; }
    .date-input-wrapper input { padding: 8px 30px 8px 12px; border: 1px solid #ccc; border-radius: 4px; outline: none; background: #fff; width: 170px; cursor: pointer; }
    .date-input-wrapper::after { content: '📅'; position: absolute; right: 10px; top: 50%; transform: translateY(-50%); pointer-events: none; font-size: 14px; }
    .btn-primary { background: #007bff; color: white; border: none; padding: 9px 20px; border-radius: 4px; cursor: pointer; font-weight: bold; transition: 0.2s; font-size: 14px;}
    .btn-primary:hover { background: #0056b3; }
    
    .table-wrapper { flex: 1; overflow: auto; border: 1px solid #eee; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; white-space: nowrap; }
    th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #eee; border-right: 1px solid #eee;}
    th { background: #fbfbfb; font-weight: bold; position: sticky; top: 0; z-index: 10; box-shadow: 0 2px 2px -1px rgba(0,0,0,0.1);}
    
    .filter-row th { background: #fff; padding: 5px 10px; top: 37px; }
    .filter-row select, .filter-row input { width: 100%; box-sizing: border-box; border: 1px solid #ddd; border-radius: 3px; padding: 4px; font-size: 12px; outline: none;}
    
    .status-closed { background: #00b300; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; display: inline-block;}
    .status-work { background: #ffcc99; color: #d35400; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; display: inline-block;}
    
    .actions-col { display: flex; gap: 5px; }
    .t-action-btn { background: #fff; border: 1px solid #ccc; border-radius: 4px; width: 28px; height: 28px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 14px; transition: 0.2s;}
    .btn-del { color: #d9534f; border-color: #ffcccc;} .btn-del:hover { background: #ffe6e6; }
    .btn-info { color: #0275d8; border-color: #cce5ff;} .btn-info:hover { background: #e6f2ff; }
    .btn-edit { color: #333; } .btn-edit:hover { background: #eee; }

    .info-modal-overlay { display: none; position: fixed; top:0; left:0; right:0; bottom:0; background: rgba(0,0,0,0.5); z-index: 2000; align-items: center; justify-content: center; }
    .info-modal-content { background: #fff; padding: 0; width: 350px; border-radius: 4px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
    .info-table { width: 100%; border-collapse: collapse; font-size: 14px;}
    .info-table td { padding: 12px 15px; border-bottom: 1px solid #eee; }
    .info-table td:first-child { color: #555; }
    .info-table td:last-child { text-align: right; }
    .info-modal-footer { padding: 15px; background: #f9f9f9; text-align: right; border-top: 1px solid #eee; border-radius: 0 0 4px 4px;}
    .info-modal-footer button { background: #e0e0e0; color: #333; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold;}
    
    .hidden-row { display: none; }
</style>

<div class="table-container">
    <div class="table-header-filters">
        <select><option>По дате создания</option></select>
        <div class="date-input-wrapper">
            <input type="text" id="ordersDateRange">
        </div>
        <button class="btn-primary" onclick="applyDateFilter()">Отчет</button>
    </div>

    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th>#</th><th>Дата</th><th>Марка</th><th>Номер</th><th>Услуги</th><th>Склад</th>
                    <th>Работник</th><th>Оплата</th><th>Контрагент</th><th>Коммент.</th><th>Скидка</th><th>Статус</th><th>Сумма</th><th>📄</th>
                </tr>
                <tr class="filter-row">
                    <th></th><th></th>
                    <th>
                        <select id="f_mark" onchange="runJSFilter()"><option value="">Все</option><option>Toyota</option><option>Kia</option><option>BMW</option><option>Mercedes</option><option>Lada</option></select>
                    </th>
                    <th><input type="text" id="f_num" oninput="runJSFilter()"></th>
                    <th></th><th></th>
                    <th>
                        <select id="f_worker" onchange="runJSFilter()"><option value="">Все</option>{% for w in workers %}<option>{{ w }}</option>{% endfor %}</select>
                    </th>
                    <th>
                        <select id="f_pay" onchange="runJSFilter()"><option value="">Все</option><option>Наличные</option><option>Карта</option><option>СБП</option><option>Перевод</option><option>Счёт</option></select>
                    </th>
                    <th><select><option value="">Все</option></select></th><th><input type="text"></th>
                    <th>
                        <select id="f_disc" onchange="runJSFilter()"><option value="">Все</option><option>0%</option><option>10%</option><option>20%</option><option>30%</option><option>40%</option><option>50%</option></select>
                    </th>
                    <th><select id="f_status" onchange="runJSFilter()"><option value="">Все</option><option value="in_work">В работе</option><option value="closed">Закрыт</option></select></th>
                    <th></th><th></th>
                </tr>
            </thead>
            <tbody id="ordersTableBody">
                {% if orders %}
                    {% for o in orders %}
                    <tr id="order-row-{{ o.id }}" class="data-row" 
                        data-mark="{{ o.mark }}" data-num="{{ o.num }}" data-master="{{ o.master }}" 
                        data-pay="{{ o.payment }}" data-disc="{{ o.discount }}" data-status="{{ o.raw_status }}">
                        <td>{{ o.index }}</td>
                        <td style="color:#666">{{ o.date_html | safe }}</td>
                        <td>{{ o.mark }}</td>
                        <td>{{ o.num }}</td>
                        <td style="white-space: normal; line-height: 1.4;">{{ o.services_html | safe }}</td>
                        <td style="white-space: normal; line-height: 1.4; color: #555;">{{ o.stock_html | safe }}</td>
                        <td>{{ o.master }}</td>
                        <td>{{ o.payment }}</td>
                        <td>{{ o.counterparty }}</td>
                        <td>{{ o.comment }}</td>
                        <td>{{ o.discount }}</td>
                        <td>{{ o.status_html | safe }}</td>
                        <td style="font-weight:bold;">{{ o.amount }} ₽</td>
                        <td>
                            <div class="actions-col">
                                <button class="t-action-btn btn-del" onclick="deleteOrder('{{ o.id }}')" title="Удалить">🗑️</button>
                                <button class="t-action-btn btn-info" onclick="openInfoModal('{{ o.id }}', '{{ o.num }}', '{{ o.raw_date }}', '{{ o.master }}')" title="Информация">ℹ️</button>
                                <button class="t-action-btn btn-edit" onclick="window.location.href='/create_order?id={{ o.id }}'" title="Редактировать">✏️</button>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr><td colspan="14" style="text-align:center; padding: 50px; color: #888;">Нет заказов в выбранном периоде</td></tr>
                {% endif %}
            </tbody>
        </table>
    </div>
</div>

<div class="info-modal-overlay" id="infoModal">
    <div class="info-modal-content">
        <table class="info-table">
            <tr><td>ID</td><td id="info_id"></td></tr>
            <tr><td>Номер</td><td id="info_num"></td></tr>
            <tr><td>Администратор</td><td id="info_admin"></td></tr>
            <tr><td>Открыт</td><td id="info_opened"></td></tr>
            <tr><td>Оплачен</td><td id="info_paid"></td></tr>
            <tr><td>Закрыт</td><td id="info_closed"></td></tr>
        </table>
        <div class="info-modal-footer">
            <button onclick="closeInfoModal()">Закрыть</button>
        </div>
    </div>
</div>

<script>
    $(function() {
        $('#ordersDateRange').daterangepicker({
            opens: 'right',
            locale: {
                format: 'DD.MM.YY', applyLabel: 'Применить', cancelLabel: 'Отмена', customRangeLabel: 'Другой',
                daysOfWeek: ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'],
                monthNames: ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'],
                firstDay: 1
            },
            ranges: {
               'Сегодня': [moment(), moment()],
               'Вчера': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
               'Последние 7 дней': [moment().subtract(6, 'days'), moment()],
               'Последние 30 дней': [moment().subtract(29, 'days'), moment()],
               'Этот месяц': [moment().startOf('month'), moment().endOf('month')],
               'Прошлый месяц': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
            },
            startDate: moment('2026-03-01'), 
            endDate: moment('2026-03-31')
        });

        {% if selected_dates %}
            $('#ordersDateRange').val("{{ selected_dates }}");
            let dates = "{{ selected_dates }}".split('-');
            if (dates.length === 2) {
                $('#ordersDateRange').data('daterangepicker').setStartDate(dates[0].trim());
                $('#ordersDateRange').data('daterangepicker').setEndDate(dates[1].trim());
            }
        {% endif %}
    });

    function applyDateFilter() {
        const dateStr = document.getElementById('ordersDateRange').value;
        window.location.href = '/orders_list?dates=' + encodeURIComponent(dateStr);
    }

    function runJSFilter() {
        let f_mark = document.getElementById('f_mark').value.toLowerCase();
        let f_num = document.getElementById('f_num').value.toLowerCase();
        let f_worker = document.getElementById('f_worker').value.toLowerCase();
        let f_pay = document.getElementById('f_pay').value.toLowerCase();
        let f_disc = document.getElementById('f_disc').value.replace('+ ', ''); 
        let f_status = document.getElementById('f_status').value;

        document.querySelectorAll('.data-row').forEach(row => {
            let r_mark = row.dataset.mark.toLowerCase();
            let r_num = row.dataset.num.toLowerCase();
            let r_master = row.dataset.master.toLowerCase();
            let r_pay = row.dataset.pay.toLowerCase();
            let r_disc = row.dataset.disc;
            let r_status = row.dataset.status;

            let show = true;
            if (f_mark && !r_mark.includes(f_mark)) show = false;
            if (f_num && !r_num.includes(f_num)) show = false;
            if (f_worker && !r_master.includes(f_worker)) show = false;
            if (f_pay && r_pay !== f_pay) show = false;
            if (f_disc && r_disc !== f_disc) show = false;
            if (f_status && r_status !== f_status) show = false;

            if (show) row.classList.remove('hidden-row');
            else row.classList.add('hidden-row');
        });
    }

    function deleteOrder(id) {
        if(confirm('Вы уверены, что хотите удалить заказ?')) {
            fetch('/api/delete_order', {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({id: id})
            }).then(res => res.json()).then(data => {
                if(data.status === 'success') document.getElementById('order-row-' + id).remove();
            });
        }
    }

    function openInfoModal(id, num, date, master) {
        document.getElementById('info_id').innerText = id;
        document.getElementById('info_num').innerText = num;
        document.getElementById('info_admin').innerText = "Все | 79131479834"; 
        document.getElementById('info_opened').innerText = date;
        document.getElementById('info_paid').innerText = date;
        
        let closedDate = date;
        try { let parts = date.split(':'); if(parts.length===2){ let m = parseInt(parts[1])+1; closedDate = parts[0] + ':' + (m<10?'0'+m:m); } } catch(e){}
        document.getElementById('info_closed').innerText = closedDate;

        document.getElementById('infoModal').style.display = 'flex';
    }

    function closeInfoModal() {
        document.getElementById('infoModal').style.display = 'none';
    }
</script>
"""

CREATE_ORDER_HTML = """
<style>
    .order-form { flex: 1; display: flex; flex-direction: column; overflow-y: auto; padding: 15px; background: #fff; }
    .top-inputs { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 10px; }
    .top-inputs input { padding: 10px; border: 1px solid #ddd; background: #fafafa; width: 100%; box-sizing: border-box; outline: none; border-radius: 4px;}
    .v-tabs { display: flex; background: #eee; margin-bottom: 10px; border-radius: 4px; overflow: hidden;}
    .v-tab { flex: 1; text-align: center; padding: 12px; cursor: pointer; font-weight: bold; color: #555; border-right: 1px solid #ddd; transition: 0.2s;}
    .v-tab.active { background: #00b300; color: white; }
    .v-tab.orange-active { background: #ff9800 !important; color: white !important; } 
    
    .r-tabs { display: flex; width: 100%; background: #f0f0f0; margin-bottom: 10px; border-radius: 4px; overflow: hidden;}
    .r-tab { flex: 1; text-align: center; padding: 10px 0; cursor: pointer; border-right: 1px solid #ddd; font-size: 14px; transition: 0.2s;}
    .r-tab.active { background: #00b300; color: white; font-weight: bold; }
    
    .services-box { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; align-content: start; overflow-y: auto; padding: 5px; flex: 1; }
    .service-item { display: flex; flex-direction: row; align-items: stretch; border: 1px solid #ddd; border-radius: 6px; background: #fff; overflow: hidden; transition: 0.2s; min-height: 40px;}
    .service-name { padding: 10px; font-size: 13px; font-weight: 500; cursor: pointer; user-select: none; flex: 1; display: flex; align-items: center; }
    .controls { display: flex; border-left: 1px solid #eee; flex-shrink: 0; }
    .controls button { width: 30px; border: none; background: #f9f9f9; cursor: pointer; font-size: 16px; font-weight: bold; color: #555; }
    .controls button:hover { background: #eee; }
    .controls input { width: 40px; text-align: center; border: none; border-left: 1px solid #eee; border-right: 1px solid #eee; font-size: 14px; outline: none; }
    
    .active-service { border-color: #00b300; background-color: #eafbee; box-shadow: 0 2px 5px rgba(0,179,0,0.2); }
    .active-service .service-name { color: #009900; font-weight: bold; }
    .active-service .controls { border-left-color: #bdf2bd; }
    .active-service .controls button { background: #d4f8d4; color: #009900; }
    .active-service .controls input { background: #eafbee; color: #009900; font-weight: bold; border-color: #bdf2bd; }
    
    .warning-service { border-color: orange !important; background-color: #fff3e0 !important; box-shadow: 0 2px 5px rgba(255,165,0,0.2) !important; }
    .warning-service .service-name { color: #d35400 !important; }
    .warning-service .controls { border-left-color: #fbdcae !important; }
    .warning-service .controls button { background: #ffe0b2 !important; color: #d35400 !important; }
    .warning-service .controls input { background: #fff3e0 !important; color: #d35400 !important; border-color: #fbdcae !important; }

    .stock-container { display: none; flex-direction: column; flex: 1; }
    .search-wrapper { position: relative; margin-bottom: 15px; }
    .search-input { width: 100%; padding: 12px; border: 2px solid #00b300; border-radius: 4px; box-sizing: border-box; outline: none; font-size: 15px; }
    .stock-dropdown { display: none; position: absolute; top: 100%; left: 0; width: 100%; max-height: 200px; overflow-y: auto; background: white; border: 1px solid #ccc; box-shadow: 0 4px 10px rgba(0,0,0,0.1); z-index: 100; border-radius: 0 0 4px 4px; }
    .stock-dropdown-item { padding: 12px; border-bottom: 1px solid #eee; cursor: pointer; display: flex; justify-content: space-between; }
    .stock-dropdown-item:hover { background: #f0f8f0; }
    #selectedStockBox { display: flex; flex-direction: column; gap: 10px; }
    .stock-row { display: flex; justify-content: space-between; align-items: center; border: 1px solid #00b300; border-radius: 6px; background: #eafbee; padding: 10px 15px; }
    .stock-row-controls { display: flex; align-items: center; gap: 15px; }
    .btn-delete { background: #ff4d4d; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 16px; display: flex; align-items: center; justify-content: center; }
    .btn-delete:hover { background: #e60000; }
    .stock-price { font-weight: bold; color: #009900; width: 80px; text-align: right; font-size: 15px;}

    .bar-wrapper { display: flex; gap: 10px; margin-top: 10px; }
    .workers-bar, .toggle-row { display: flex; background: #eee; border-radius: 4px; overflow: hidden; flex: 1; }
    .worker-btn, .t-btn { flex: 1; text-align: center; padding: 12px; border-right: 1px solid #ddd; cursor: pointer; font-size: 14px; color: #555; transition: 0.2s; user-select: none;}
    .worker-btn.active, .t-btn.active-green { background: #00b300; color: white; font-weight: bold; }
    .gear-btn { min-width: 50px; width: 50px; background: #ddd; color: #333; font-size: 20px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: 0.2s; border-radius: 4px; flex-shrink: 0; z-index: 10;}
    .gear-btn:hover { background: #ccc; }
    .locked-bar { opacity: 0.4; pointer-events: none; filter: grayscale(100%); }

    .bottom-split { display: flex; gap: 20px; padding: 15px; background: white; border-top: 1px solid #ddd; flex-shrink: 0; }
    .half { flex: 1; display: flex; flex-direction: column; justify-content: space-between; gap: 10px; }
    .flex-row { display: flex; gap: 10px; height: 50px; }
    .action-btn { font-weight: bold; border: none; border-radius: 4px; cursor: pointer; color: white; text-align: center; text-decoration: none; flex: 1; font-size: 16px; display: flex; align-items: center; justify-content: center; }
    .bg-blue { background: #007bff; } .bg-green { background: #00b300; }
    .status-badge { background: #ffcc99; color: #d35400; flex: 1; display: flex; align-items: center; justify-content: center; border-radius: 4px; font-weight: bold; font-size: 16px; }
    .total-price-display { font-size: 24px; font-weight: bold; color: #00b300; display: flex; align-items: center; justify-content: flex-end; flex: 1;}

    .modal-overlay { display: none; position: fixed; top:0; left:0; right:0; bottom:0; background: rgba(0,0,0,0.5); z-index: 2000; align-items: center; justify-content: center; }
    .modal-content { background: #fff; padding: 25px; width: 600px; max-height: 80vh; overflow-y: auto; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
    .modal-content h3 { margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 10px; }
    .srv-worker-group { margin-bottom: 15px; border-bottom: 1px dashed #eee; padding-bottom: 10px; }
    .modal-close-btn { background: #00b300; color: white; border: none; padding: 12px; font-weight: bold; border-radius: 4px; cursor: pointer; flex: 1; font-size: 16px; }
    .modal-reset-btn { background: #ff4d4d; color: white; border: none; padding: 12px; font-weight: bold; border-radius: 4px; cursor: pointer; flex: 1; font-size: 16px; }
</style>

<div class="order-form">
    <div class="top-inputs">
        <input type="text" id="dateTimeInput" placeholder="Дата/Время" value="{{ order.date if order else '' }}">
        <input type="text" id="numInput" placeholder="Номер" value="{{ order.num if order else '' }}">
        <input type="text" id="markInput" placeholder="Марка" value="{{ order.mark if order else '' }}">
        <input type="text" id="nameInput" placeholder="Имя" value="{{ order.name if order else '' }}">
        <input type="text" id="phoneInput" placeholder="Телефон" oninput="formatPhone(this)" value="{{ order.phone if order else '' }}">
        <input type="text" id="modelInput" placeholder="Модель" value="{{ order.model if order else '' }}">
    </div>

    <div class="v-tabs">
        <div class="v-tab active" onclick="switchType('car', this)">Легковые</div>
        <div class="v-tab" onclick="switchType('jeep', this)">Внедорожники</div>
        <div class="v-tab" onclick="switchType('truck', this)">Грузовые</div>
        <div class="v-tab" onclick="switchType('stock', this)">Склад</div>
    </div>

    <div class="r-tabs" id="radiusTabs">
        <div class="r-tab" onclick="selectRadius(this)">R13</div>
        <div class="r-tab" onclick="selectRadius(this)">R14</div>
        <div class="r-tab" onclick="selectRadius(this)">R15</div>
        <div class="r-tab active" onclick="selectRadius(this)">R16</div>
        <div class="r-tab" onclick="selectRadius(this)">R17</div>
        <div class="r-tab" onclick="selectRadius(this)">R18</div>
        <div class="r-tab" onclick="selectRadius(this)">R19</div>
        <div class="r-tab" onclick="selectRadius(this)">R20</div>
        <div class="r-tab" onclick="selectRadius(this)">R21</div>
        <div class="r-tab" onclick="selectRadius(this)">R22</div>
    </div>

    <div class="services-box" id="carBox"></div>
    <div class="services-box" id="truckBox" style="display: none;"></div>

    <div class="stock-container" id="stockContainer">
        <div class="search-wrapper">
            <input type="text" id="stockSearch" class="search-input" placeholder="Нажмите для поиска запчастей..." onclick="toggleStockDropdown(true)" oninput="filterStockDropdown()">
            <div class="stock-dropdown" id="stockDropdown"></div>
        </div>
        <div id="selectedStockBox"></div>
        <div id="stockTotalDisplay" style="text-align: right; padding: 15px 5px; font-weight: bold; color: #00b300; font-size: 16px; border-top: 1px solid #eee; margin-top: 10px;">Сумма запчастей: 0 ₽</div>
    </div>

    <div class="bar-wrapper">
        <div class="workers-bar" id="globalWorkerBar">
            {% for w in workers %}
                <div class="worker-btn" onclick="toggleGlobalWorker(this)">{{ w }}</div>
            {% endfor %}
        </div>
        <button class="gear-btn" onclick="openWorkerModal()" title="Детальная настройка работников">⚙️</button>
    </div>
</div>

<div class="bottom-split">
    <div class="half">
        <div class="toggle-row">
            <div class="t-btn p-btn active-green" onclick="selectPayment(this, 'Наличные')">Наличные</div>
            <div class="t-btn p-btn" onclick="selectPayment(this, 'Карта')">Карта</div>
            <div class="t-btn p-btn" onclick="selectPayment(this, 'СБП')">СБП</div>
            <div class="t-btn p-btn" onclick="selectPayment(this, 'Перевод')">Перевод</div>
            <div class="t-btn p-btn" onclick="selectPayment(this, 'Счёт')">Счёт</div>
        </div>
        
        <div class="bar-wrapper" style="margin-top: 0;">
            <div class="toggle-row" id="globalDiscountBar" style="margin-top: 0;">
                <div class="t-btn d-btn active-green" onclick="selectDiscount(this, 0)">0%</div>
                <div class="t-btn d-btn" onclick="selectDiscount(this, 10)">10%</div>
                <div class="t-btn d-btn" onclick="selectDiscount(this, 20)">20%</div>
                <div class="t-btn d-btn" onclick="selectDiscount(this, 30)">30%</div>
                <div class="t-btn d-btn" onclick="selectDiscount(this, 40)">40%</div>
                <div class="t-btn d-btn" onclick="selectDiscount(this, 50)">50%</div>
            </div>
            <button class="gear-btn" onclick="openDiscountModal()" title="Детальная настройка скидок">⚙️</button>
        </div>

        <input type="text" placeholder="Комментарий" style="width: 100%; padding: 12px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; outline: none; background: #fafafa;">
    </div>
    
    <div class="half">
        <div class="flex-row">
            <div class="status-badge">Не оплачено</div>
            <div class="total-price-display" id="totalPrice">{{ order.amount if order else '0' }} ₽</div>
        </div>
        <div class="flex-row">
            <button class="action-btn bg-blue" onclick="saveOrderToServer()">Сохранить</button>
            <a href="/checkout?status=in_work" class="action-btn bg-green">Закрыть</a>
        </div>
    </div>
</div>

<div class="modal-overlay" id="workerModal">
    <div class="modal-content">
        <h3>Исполнители услуг</h3>
        <div id="workerModalBody"></div>
        <div style="display: flex; gap: 10px; margin-top: 15px;">
            <button class="modal-reset-btn" onclick="resetWorkerModal()">Сбросить (Общие)</button>
            <button class="modal-close-btn" onclick="saveWorkerModal()">Сохранить исполнителей</button>
        </div>
    </div>
</div>

<div class="modal-overlay" id="discountModal">
    <div class="modal-content">
        <h3>Индивидуальные скидки на услуги</h3>
        <div id="discountModalBody"></div>
        <div style="display: flex; gap: 10px; margin-top: 15px;">
            <button class="modal-reset-btn" onclick="resetDiscountModal()">Сбросить (Общая)</button>
            <button class="modal-close-btn" onclick="saveDiscountModal()">Сохранить скидки</button>
        </div>
    </div>
</div>

<script>
    const WORKERS_LIST = {{ workers | tojson | safe }};
    const priceMatrix = {{ prices_json | safe }};
    const stockItemsDb = {{ stock_json | safe }};
    const savedOrder = {{ order | tojson | safe if order else 'null' }};
    
    let currentType = 'car';
    let currentRadius = 'R16';
    let currentGlobalDiscount = 0;
    let currentPaymentMethod = 'Наличные';
    
    let isWorkerPerService = false;
    let perServiceWorkers = {};
    let isDiscountPerService = false;
    let perServiceDiscounts = {};
    
    const srvNames = {
        'car': { 'srv1':'Снятие и установка', 'srv2':'Балансировка', 'srv3':'Снятие | Установка | Балансировка', 'srv4':'Комплекс 1* колеса', 'srv5':'Комплекс 4* колеса', 'srv6':'Правка дисков', 'srv7':'Монтаж', 'srv8':'Демонтаж', 'srv9':'Демонтаж и монтаж', 'srv10':'Покраска дисков' },
        'truck': { 'tr1':'Снятие/Установка (Вед)', 'tr2':'Снятие/Установка (Рул)', 'tr3':'Балансировка', 'tr4':'С/У/Баланс (Вед)', 'tr5':'С/У/Баланс (Рул)', 'tr6':'Комплекс 1* (Вед)', 'tr7':'Комплекс 1* (Рул)', 'tr8':'Монтаж', 'tr9':'Демонтаж', 'tr10':'Демонтаж и монтаж', 'tr11':'Нарезка протектора' }
    };

    document.addEventListener("DOMContentLoaded", function() {
        if (savedOrder) {
            document.getElementById('dateTimeInput').value = savedOrder.date;
            document.getElementById('numInput').value = savedOrder.num;
            document.getElementById('markInput').value = savedOrder.mark;
            document.getElementById('nameInput').value = savedOrder.name;
            document.getElementById('phoneInput').value = savedOrder.phone;
            document.getElementById('modelInput').value = savedOrder.model;
            
            currentType = savedOrder.type_id || 'car';
            currentRadius = savedOrder.radius || 'R16';
            currentPaymentMethod = savedOrder.payment_method || 'Наличные';
            
            if (savedOrder.per_service_workers && Object.keys(savedOrder.per_service_workers).length > 0) {
                perServiceWorkers = savedOrder.per_service_workers;
                isWorkerPerService = true;
                document.getElementById('globalWorkerBar').classList.add('locked-bar');
            }
            if (savedOrder.per_service_discounts && Object.keys(savedOrder.per_service_discounts).length > 0) {
                perServiceDiscounts = savedOrder.per_service_discounts;
                isDiscountPerService = true;
                document.getElementById('globalDiscountBar').classList.add('locked-bar');
            } else {
                currentGlobalDiscount = savedOrder.discount || 0;
            }
            
            let tabNames = {'car': 'Легковые', 'jeep': 'Внедорожники', 'truck': 'Грузовые'};
            document.querySelectorAll('.v-tab').forEach(t => {
                t.classList.remove('active');
                if(t.innerText === tabNames[currentType]) t.classList.add('active');
            });
            document.querySelectorAll('.r-tab').forEach(t => {
                t.classList.remove('active');
                if(t.innerText === currentRadius) t.classList.add('active');
            });
            
            let discBtn = document.querySelector(`.d-btn[onclick*="${currentGlobalDiscount}"]`);
            if(discBtn) {
                document.querySelectorAll('.d-btn').forEach(t => t.classList.remove('active-green'));
                discBtn.classList.add('active-green');
            }
            
            let payBtn = document.querySelector(`.p-btn[onclick*="${currentPaymentMethod}"]`);
            if(payBtn) {
                document.querySelectorAll('.p-btn').forEach(t => t.classList.remove('active-green'));
                payBtn.classList.add('active-green');
            }

            renderServices();

            if(savedOrder.services) {
                for(let id in savedOrder.services) {
                    let inp = document.getElementById(id);
                    if(inp) {
                        inp.value = savedOrder.services[id];
                        if(inp.hasAttribute('placeholder')) inp.dataset.active = 'true';
                        updateHighlight(id);
                    }
                }
            }
            
            if(savedOrder.stock) {
                for(let id in savedOrder.stock) {
                    addStockItem(id);
                    let inp = document.getElementById(id);
                    if(inp) {
                        inp.value = savedOrder.stock[id];
                        validateInput(inp);
                    }
                }
            }
            
            if (!isWorkerPerService) {
                let savedMasters = savedOrder.master.split(', ');
                document.querySelectorAll('#globalWorkerBar .worker-btn').forEach(btn => {
                    if (savedMasters.includes(btn.innerText.trim())) btn.classList.add('active');
                });
            }
            
        } else {
            let now = new Date();
            let d = String(now.getDate()).padStart(2, '0'), m = String(now.getMonth() + 1).padStart(2, '0');
            let y = String(now.getFullYear()).slice(-2), h = String(now.getHours()).padStart(2, '0'), min = String(now.getMinutes()).padStart(2, '0');
            document.getElementById('dateTimeInput').value = `${d}.${m}.${y} ${h}:${min}`;
            renderServices();
        }
        calcTotal();
    });

    function renderServices() {
        const carBox = document.getElementById('carBox');
        const truckBox = document.getElementById('truckBox');
        const box = currentType === 'truck' ? truckBox : carBox;
        
        let tempVals = {};
        box.querySelectorAll('.srv-input').forEach(inp => {
            tempVals[inp.id] = { val: inp.value, active: inp.dataset.active };
        });

        let html = '';
        let baseGrp = currentType === 'truck' ? 'truck' : 'car'; 
        let priceGrp = (currentType === 'car' || currentType === 'jeep') ? priceMatrix[currentType][currentRadius] : priceMatrix['truck']['default'];

        for (let srvId in srvNames[baseGrp]) {
            let name = srvNames[baseGrp][srvId];
            let price = priceGrp[srvId];
            
            if (srvId === 'srv6') { 
                html += `<div class="service-item" id="row-${srvId}">
                           <div class="service-name" onclick="toggleService('${srvId}', true)">▶ ${name}</div>
                           <div class="controls"><input type="number" class="srv-input" id="${srvId}" placeholder="Цена ₽" oninput="updateHighlight('${srvId}'); calcTotal();" data-active="false" style="width:70px;"></div>
                         </div>`;
            } else {
                html += `<div class="service-item" id="row-${srvId}">
                           <div class="service-name" onclick="toggleService('${srvId}', false)">▶ ${name} <span style="color:#aaa; font-size:11px;">(${price}₽)</span></div>
                           <div class="controls">
                               <button onclick="changeVal('${srvId}', -1)">-</button>
                               <input type="number" class="srv-input" id="${srvId}" value="0" min="0" data-price="${price}" oninput="validateInput(this); updateHighlight('${srvId}')">
                               <button onclick="changeVal('${srvId}', 1)">+</button>
                           </div>
                         </div>`;
            }
        }
        box.innerHTML = html;

        for (let id in tempVals) {
            let inp = document.getElementById(id);
            if (inp) {
                inp.value = tempVals[id].val;
                inp.dataset.active = tempVals[id].active;
                updateHighlight(id);
            }
        }
    }

    function switchType(type, el) {
        document.querySelectorAll('.v-tab').forEach(t => { t.classList.remove('active'); t.classList.remove('orange-active'); });
        el.classList.add('active');
        const rTabs = document.getElementById('radiusTabs');
        
        if (type !== 'stock') {
            currentType = type; 
            rTabs.style.display = 'flex';
        } else {
            let tabNames = {'car': 'Легковые', 'jeep': 'Внедорожники', 'truck': 'Грузовые'};
            document.querySelectorAll('.v-tab').forEach(t => { if(t.innerText === tabNames[currentType]) t.classList.add('orange-active'); });
            rTabs.style.display = 'none'; 
        }
        
        document.getElementById('carBox').style.display = 'none';
        document.getElementById('truckBox').style.display = 'none';
        document.getElementById('stockContainer').style.display = 'none';
        
        if (type === 'car' || type === 'jeep') {
            document.getElementById('carBox').style.display = 'grid';
            renderServices(); 
        } else if (type === 'truck') {
            document.getElementById('truckBox').style.display = 'grid';
            renderServices();
        } else if (type === 'stock') {
            document.getElementById('stockContainer').style.display = 'flex';
        }
        calcTotal();
    }

    function selectRadius(el) {
        document.querySelectorAll('.r-tab').forEach(t => t.classList.remove('active'));
        el.classList.add('active');
        currentRadius = el.innerText.trim();
        renderServices();
        calcTotal();
    }

    function selectPayment(el, method) {
        document.querySelectorAll('.p-btn').forEach(t => t.classList.remove('active-green'));
        el.classList.add('active-green');
        currentPaymentMethod = method;
    }
    
    function selectDiscount(el, val) {
        if(isDiscountPerService) return;
        document.querySelectorAll('.d-btn').forEach(t => t.classList.remove('active-green'));
        el.classList.add('active-green');
        currentGlobalDiscount = val;
        calcTotal();
    }

    function calcTotal() {
        let total = 0;
        let stockTotal = 0;
        
        document.querySelectorAll('.srv-input').forEach(inp => {
            let val = parseInt(inp.value) || 0;
            let price = parseInt(inp.dataset.price) || 0;
            let rowId = inp.id;
            let isActive = inp.hasAttribute('placeholder') ? (inp.dataset.active === 'true' || val > 0) : (val > 0);

            if (isActive) {
                let cost = inp.hasAttribute('placeholder') ? val : val * price;
                let itemDiscount = isDiscountPerService ? (perServiceDiscounts[rowId] || 0) : currentGlobalDiscount;
                total += cost * (1 - itemDiscount / 100);
            }
        });
        
        document.querySelectorAll('.stock-input').forEach(inp => {
            let val = parseInt(inp.value) || 0;
            let price = parseInt(inp.dataset.price) || 0;
            let rowPrice = val * price;
            let priceDisplay = document.getElementById('price-' + inp.id);
            if(priceDisplay) priceDisplay.innerText = rowPrice + ' ₽';
            stockTotal += rowPrice;
        });

        document.getElementById('stockTotalDisplay').innerText = 'Сумма запчастей: ' + stockTotal + ' ₽';
        document.getElementById('totalPrice').innerText = Math.round(total + stockTotal) + ' ₽';
        checkWarnings();
    }

    function checkWarnings() {
        let globalWorkersCount = document.querySelectorAll('#globalWorkerBar .worker-btn.active').length;
        document.querySelectorAll('.active-service').forEach(row => {
            let srvId = row.id.replace('row-', '');
            let hasSpecificWorker = perServiceWorkers[srvId] && perServiceWorkers[srvId].length > 0;
            let hasGlobalWorker = globalWorkersCount > 0 && !isWorkerPerService; 
            
            if (!hasSpecificWorker && !hasGlobalWorker) row.classList.add('warning-service');
            else row.classList.remove('warning-service');
        });
    }

    function toggleGlobalWorker(el) {
        if(isWorkerPerService) return;
        el.classList.toggle('active');
        checkWarnings();
    }

    function changeVal(id, delta) {
        let input = document.getElementById(id);
        let val = parseInt(input.value) || 0;
        val += delta;
        if (input.classList.contains('stock-input')) { if (val < 1) val = 1; } 
        else { if (val < 0) val = 0; }
        input.value = val;
        updateHighlight(id);
        calcTotal();
    }

    function toggleService(id, isPrice = false) {
        let input = document.getElementById(id);
        if (isPrice) {
            if (input.dataset.active === 'true') { input.dataset.active = 'false'; input.value = ''; } 
            else { input.dataset.active = 'true'; if (!input.value || input.value == '0') input.value = 2000; input.focus(); }
        } else {
            let val = parseInt(input.value) || 0;
            input.value = val > 0 ? 0 : 1;
        }
        
        let isActiveNow = isPrice ? (input.dataset.active === 'true') : (parseInt(input.value) > 0);
        if (isActiveNow) {
            if (!perServiceWorkers[id]) perServiceWorkers[id] = [];
            if (!perServiceDiscounts[id]) perServiceDiscounts[id] = 0;
        }

        updateHighlight(id);
        calcTotal();
    }

    function updateHighlight(id) {
        let input = document.getElementById(id);
        let row = document.getElementById('row-' + id);
        if(!row) return; 
        let isActive = input.hasAttribute('placeholder') ? (input.dataset.active === 'true' || parseInt(input.value) > 0) : (parseInt(input.value) > 0);
        if (isActive) row.classList.add('active-service'); 
        else row.classList.remove('active-service');
    }

    function validateInput(el) { 
        let val = Math.abs(parseInt(el.value)) || 0; 
        if (el.classList.contains('stock-input') && val < 1) val = 1;
        el.value = val; 
        calcTotal(); 
    }
    
    function formatPhone(input) {
        let val = input.value.replace(/\\D/g, '');
        if (val.length === 0) { input.value = ''; return; }
        let prefix = '+7 ';
        if (val[0] === '7' || val[0] === '8') val = val.substring(1);
        let formatted = prefix;
        if (val.length > 0) formatted += '(' + val.substring(0, 3);
        if (val.length >= 4) formatted += ')-' + val.substring(3, 6);
        if (val.length >= 7) formatted += '-' + val.substring(6, 8);
        if (val.length >= 9) formatted += '-' + val.substring(8, 10);
        input.value = formatted;
    }

    function openWorkerModal() {
        try {
            let html = '';
            document.querySelectorAll('.active-service').forEach(row => {
                if(!row.id.startsWith('row-srv') && !row.id.startsWith('row-tr')) return; 
                let nameEl = row.querySelector('.service-name');
                if(!nameEl) return;
                
                let srvName = nameEl.innerText.replace('▶ ', '');
                let srvId = row.id.replace('row-', '');
                if (!perServiceWorkers[srvId]) perServiceWorkers[srvId] = [];
                
                html += `<div class="srv-worker-group"><strong style="color: #00b300; font-size: 15px;">${srvName}</strong><div class="workers-bar" style="margin-top: 8px;">`;
                WORKERS_LIST.forEach(w => {
                    let activeCls = perServiceWorkers[srvId].includes(w) ? 'active' : '';
                    html += `<div class="worker-btn ${activeCls}" onclick="toggleModalWorker(this, '${srvId}', '${w}')">${w}</div>`;
                });
                html += `</div></div>`;
            });
            if(!html) html = '<p style="color:#888;">Сначала выберите хотя бы одну услугу.</p>';
            document.getElementById('workerModalBody').innerHTML = html;
            document.getElementById('workerModal').style.display = 'flex';
        } catch (e) { console.error(e); }
    }

    function toggleModalWorker(el, srvId, workerName) {
        el.classList.toggle('active');
        if (el.classList.contains('active')) {
            if (!perServiceWorkers[srvId].includes(workerName)) perServiceWorkers[srvId].push(workerName);
        } else {
            perServiceWorkers[srvId] = perServiceWorkers[srvId].filter(w => w !== workerName);
        }
    }

    function saveWorkerModal() {
        isWorkerPerService = true;
        document.getElementById('globalWorkerBar').classList.add('locked-bar');
        document.getElementById('workerModal').style.display = 'none';
        checkWarnings();
    }
    
    function resetWorkerModal() {
        isWorkerPerService = false;
        perServiceWorkers = {};
        document.getElementById('globalWorkerBar').classList.remove('locked-bar');
        document.getElementById('workerModal').style.display = 'none';
        checkWarnings();
    }

    function openDiscountModal() {
        try {
            let html = '';
            document.querySelectorAll('.active-service').forEach(row => {
                if(!row.id.startsWith('row-srv') && !row.id.startsWith('row-tr')) return; 
                let nameEl = row.querySelector('.service-name');
                if(!nameEl) return;
                
                let srvName = nameEl.innerText.replace('▶ ', '');
                let srvId = row.id.replace('row-', '');
                let curVal = perServiceDiscounts[srvId] || 0;
                
                html += `<div class="srv-worker-group"><strong style="color: #00b300; font-size: 15px;">${srvName}</strong><div class="toggle-row" style="margin-top: 8px;">`;
                [0, 10, 20, 30, 40, 50].forEach(val => {
                    let actCls = (curVal === val) ? 'active-green' : '';
                    html += `<div class="t-btn d-btn-mod ${actCls}" onclick="setModalDiscount(this, '${srvId}', ${val})">${val}%</div>`;
                });
                html += `</div></div>`;
            });
            if(!html) html = '<p style="color:#888;">Сначала выберите хотя бы одну услугу.</p>';
            document.getElementById('discountModalBody').innerHTML = html;
            document.getElementById('discountModal').style.display = 'flex';
        } catch (e) { console.error(e); }
    }

    function setModalDiscount(el, srvId, val) {
        let parent = el.closest('.toggle-row');
        parent.querySelectorAll('.d-btn-mod').forEach(b => b.classList.remove('active-green'));
        el.classList.add('active-green');
        perServiceDiscounts[srvId] = val;
    }

    function saveDiscountModal() {
        isDiscountPerService = true;
        document.getElementById('globalDiscountBar').classList.add('locked-bar');
        document.getElementById('discountModal').style.display = 'none';
        calcTotal();
    }
    
    function resetDiscountModal() {
        isDiscountPerService = false;
        perServiceDiscounts = {};
        document.getElementById('globalDiscountBar').classList.remove('locked-bar');
        document.getElementById('discountModal').style.display = 'none';
        calcTotal();
    }

    function toggleStockDropdown(show) {
        if(show) { 
            document.getElementById('stockDropdown').style.display = 'block'; 
            filterStockDropdown(); 
        } 
    }

    function filterStockDropdown() {
        let input = document.getElementById('stockSearch').value.toLowerCase();
        let html = '';
        stockItemsDb.forEach(item => {
            if(item.name.toLowerCase().includes(input)) {
                html += `<div class="stock-dropdown-item" onclick="addStockItem('${item.id}')">
                            <span>${item.name}</span>
                            <span style="color:#00b300; font-weight:bold;">${item.price} ₽</span>
                         </div>`;
            }
        });
        document.getElementById('stockDropdown').innerHTML = html || '<div style="padding:10px; color:#888;">Ничего не найдено</div>';
    }

    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-wrapper')) document.getElementById('stockDropdown').style.display = 'none';
    });

    function addStockItem(id) {
        const item = stockItemsDb.find(i => i.id === id);
        const box = document.getElementById('selectedStockBox');
        
        document.getElementById('stockSearch').value = '';
        document.getElementById('stockDropdown').style.display = 'none';

        if(document.getElementById(id)) { changeVal(id, 1); return; }

        let card = document.createElement('div');
        card.className = 'stock-row';
        card.id = 'row-' + id;
        card.innerHTML = `
            <div style="font-weight: bold; font-size: 15px; color: #009900;">${item.name}</div>
            <div class="stock-row-controls">
                <button class="btn-delete" onclick="removeStockItem('${id}')">🗑</button>
                <div style="display: flex; border: 1px solid #bdf2bd; border-radius: 4px; overflow: hidden; background: #fff;">
                    <button onclick="changeVal('${id}', -1)" style="border: none; background: #f9f9f9; width: 30px; font-weight: bold; cursor: pointer;">-</button>
                    <input type="number" class="stock-input" id="${id}" value="1" min="1" data-price="${item.price}" oninput="validateInput(this)" style="width: 40px; text-align: center; border: none; font-size: 15px; outline: none;">
                    <button onclick="changeVal('${id}', 1)" style="border: none; background: #f9f9f9; width: 30px; font-weight: bold; cursor: pointer;">+</button>
                </div>
                <div class="stock-price" id="price-${id}">${item.price} ₽</div>
            </div>
        `;
        box.appendChild(card);
        calcTotal();
    }

    function removeStockItem(id) {
        let row = document.getElementById('row-' + id);
        if(row) row.remove();
        calcTotal();
    }

    function saveOrderToServer() {
        let urlParams = new URLSearchParams(window.location.search);
        let orderId = urlParams.get('id');

        let tabNames = {'car': 'Легковые', 'jeep': 'Внедорожники', 'truck': 'Грузовые'};
        let actualTypeName = tabNames[currentType]; 

        let globalWorkers = Array.from(document.querySelectorAll('#globalWorkerBar .worker-btn.active')).map(e => e.innerText);
        
        let servicesDict = {};
        document.querySelectorAll('.srv-input').forEach(inp => {
            let val = parseInt(inp.value) || 0;
            let isActive = inp.hasAttribute('placeholder') ? (inp.dataset.active === 'true' || val > 0) : (val > 0);
            if (isActive) servicesDict[inp.id] = val;
        });

        let stockDict = {};
        document.querySelectorAll('.stock-input').forEach(inp => {
            let val = parseInt(inp.value) || 0;
            if (val > 0) stockDict[inp.id] = val;
        });

        let finalMaster = "Не назначен";
        if (isWorkerPerService) {
            let allIndivWorkers = new Set();
            for (let key in perServiceWorkers) {
                perServiceWorkers[key].forEach(w => allIndivWorkers.add(w));
            }
            if(allIndivWorkers.size > 0) finalMaster = Array.from(allIndivWorkers).join(', ') + ' (Инд.)';
        } else if (globalWorkers.length > 0) {
            finalMaster = globalWorkers.join(', ');
        }

        let payload = {
            id: orderId,
            date: document.getElementById('dateTimeInput').value,
            num: document.getElementById('numInput').value,
            mark: document.getElementById('markInput').value,
            name: document.getElementById('nameInput').value,
            phone: document.getElementById('phoneInput').value,
            model: document.getElementById('modelInput').value,
            type: actualTypeName,
            type_id: currentType,
            radius: currentRadius,
            discount: currentGlobalDiscount,
            payment_method: currentPaymentMethod,
            master: finalMaster,
            amount: document.getElementById('totalPrice').innerText,
            services: servicesDict,
            stock: stockDict,
            per_service_workers: isWorkerPerService ? perServiceWorkers : {},
            per_service_discounts: isDiscountPerService ? perServiceDiscounts : {}
        };

        fetch('/api/save_order', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        }).then(res => res.json()).then(data => {
            if(data.status === 'success') window.location.href = '/checkout?status=in_work';
            else alert('Ошибка при сохранении');
        }).catch(err => alert('Сетевая ошибка при сохранении'));
    }
</script>
"""

# ==========================================
# РОУТЫ (МАРШРУТИЗАЦИЯ)
# ==========================================

@app.route('/')
def index():
    if 'user' in session: return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form.get('phone', '+7 (932)-322-22-12')
        return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(BASE_HTML, content=render_template_string(DASHBOARD_HTML, workers=WORKERS_DB), current_tab='dashboard', show_topbar=False, kassa=get_kassa_totals())

@app.route('/api/get_report', methods=['POST'])
def get_report_api():
    if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    req = request.json
    start_date_str = req.get('start', '').strip()
    end_date_str = req.get('end', '').strip()
    worker_filter = req.get('worker') 

    try:
        start_date = datetime.strptime(start_date_str, '%d.%m.%y')
        end_date = datetime.strptime(end_date_str + ' 23:59:59', '%d.%m.%y %H:%M:%S')
    except Exception as e:
        start_date = datetime.min
        end_date = datetime.max

    stats = {
        'cash': 0, 'cash_count': 0, 'invoice': 0, 'invoice_count': 0,
        'card': 0, 'card_count': 0, 'transfer': 0, 'transfer_count': 0,
        'd30': 0, 'd30_count': 0, 'd20': 0, 'd20_count': 0, 'd10': 0, 'd10_count': 0,
        'total_orders': 0, 'total_orders_count': 0, 'total_disc': 0, 'total_disc_count': 0
    }

    for o in ORDERS_DB['closed']:
        try:
            order_date = datetime.strptime(o['date'], '%d.%m.%y %H:%M')
            if not (start_date <= order_date <= end_date): continue
        except: continue 
            
        if worker_filter and worker_filter != "(Все)" and worker_filter not in o.get('master', ''): continue
                
        amt = int(str(o.get('amount', '0')).replace(' ₽', '').replace(' ', ''))
        pay_method = o.get('payment_method', 'Наличные')
        disc = int(o.get('discount', 0))

        stats['total_orders'] += amt
        stats['total_orders_count'] += 1

        if pay_method == 'Наличные': stats['cash'] += amt; stats['cash_count'] += 1
        elif pay_method == 'Карта': stats['card'] += amt; stats['card_count'] += 1
        elif pay_method == 'Счёт': stats['invoice'] += amt; stats['invoice_count'] += 1
        elif pay_method == 'Перевод': stats['transfer'] += amt; stats['transfer_count'] += 1

        if disc > 0:
            disc_rubles = int((amt / (1 - disc/100)) * (disc/100))
            stats['total_disc'] += disc_rubles
            stats['total_disc_count'] += 1
            if disc == 10: stats['d10'] += disc_rubles; stats['d10_count'] += 1
            elif disc == 20: stats['d20'] += disc_rubles; stats['d20_count'] += 1
            elif disc == 30: stats['d30'] += disc_rubles; stats['d30_count'] += 1

    avg = stats['total_orders'] / stats['total_orders_count'] if stats['total_orders_count'] > 0 else 0
        
    return jsonify({
        'cash': f"{stats['cash']:,} ₽".replace(',', ' '), 'cash_count': stats['cash_count'],
        'invoice': f"{stats['invoice']:,} ₽".replace(',', ' '), 'invoice_count': stats['invoice_count'],
        'card': f"{stats['card']:,} ₽".replace(',', ' '), 'card_count': stats['card_count'],
        'transfer': f"{stats['transfer']:,} ₽".replace(',', ' '), 'transfer_count': stats['transfer_count'],
        'total_orders': f"{stats['total_orders']:,} ₽".replace(',', ' '), 'total_orders_count': stats['total_orders_count'],
        'salary': '0 ₽', 'other_exp': '0 ₽', 'total_exp': '0 ₽', 
        'avg_check': f"{avg:,.2f} ₽".replace(',', ' '), 'obj_load': '0,00 %', 'worker_load': '0,00 %',
        'd30': f"{stats['d30']:,} ₽".replace(',', ' '), 'd30_count': stats['d30_count'],
        'd20': f"{stats['d20']:,} ₽".replace(',', ' '), 'd20_count': stats['d20_count'],
        'd10': f"{stats['d10']:,} ₽".replace(',', ' '), 'd10_count': stats['d10_count'],
        'total_disc': f"{stats['total_disc']:,} ₽".replace(',', ' '), 'total_disc_count': stats['total_disc_count']
    })

def format_orders_for_table(orders_list):
    result = []
    for idx, o in enumerate(orders_list):
        base_grp = 'truck' if o.get('type_id') == 'truck' else 'car'
        
        srv_list = []
        for s_id, qty in o.get('services', {}).items():
            name = SRV_NAMES[base_grp].get(s_id, s_id)
            if base_grp == 'car' and o.get('radius'): name += f" {o['radius']}"
            if qty > 1: name += f" x {qty}"
            srv_list.append(f"▶ {name}")

        stk_list = []
        for s_id, qty in o.get('stock', {}).items():
            name = STOCK_MAP.get(s_id, s_id)
            stk_list.append(name)

        date_parts = o.get('date', '').split(' ')
        date_html = f"{date_parts[0]}<br><span style='color:#888; font-size:12px;'>{date_parts[1] if len(date_parts)>1 else ''}</span>"
        status_html = '<span class="status-closed">Закрыт</span>' if o.get('status') == 'closed' else '<span class="status-work">В работе</span>'

        result.append({
            'index': o.get('id') if len(str(o.get('id'))) < 5 else idx + 1,
            'id': o.get('id'),
            'date_html': date_html,
            'raw_date': o.get('date', ''),
            'mark': o.get('mark', ''),
            'num': o.get('num', 'БН') or 'БН',
            'services_html': '<br>'.join(srv_list) or '—',
            'stock_html': '<br>'.join(stk_list),
            'master': o.get('master', ''),
            'payment': o.get('payment_method', ''),
            'discount': f"{o.get('discount')}%" if o.get('discount', 0) else '',
            'amount': o.get('amount', '0'),
            'status_html': status_html,
            'raw_status': o.get('status', 'in_work')
        })
    return result

@app.route('/orders_list')
def orders_list():
    if 'user' not in session: return redirect(url_for('login'))
    
    dates_param = request.args.get('dates')
    all_raw_data = ORDERS_DB['in_work'] + ORDERS_DB['closed']
    
    if dates_param:
        try:
            start_str, end_str = dates_param.split(' - ')
            start_date = datetime.strptime(start_str.strip(), '%d.%m.%y')
            end_date = datetime.strptime(end_str.strip() + ' 23:59:59', '%d.%m.%y %H:%M:%S')
            
            filtered_data = []
            for o in all_raw_data:
                try:
                    o_date = datetime.strptime(o['date'], '%d.%m.%y %H:%M')
                    if start_date <= o_date <= end_date:
                        filtered_data.append(o)
                except: pass
            all_raw_data = filtered_data
        except: pass
            
    formatted_data = format_orders_for_table(all_raw_data)
    return render_template_string(BASE_HTML, content=render_template_string(ORDERS_FULL_TABLE_HTML, orders=formatted_data, workers=WORKERS_DB, selected_dates=dates_param), current_tab='orders_list', show_topbar=False, kassa=get_kassa_totals())

@app.route('/checkout')
def checkout():
    if 'user' not in session: return redirect(url_for('login'))
    status = request.args.get('status', 'in_work')
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    recent_orders = []
    for o in ORDERS_DB.get(status, []):
        try:
            o_date = datetime.strptime(o['date'], '%d.%m.%y %H:%M').date()
            if o_date in [today, yesterday]: recent_orders.append(o)
        except: pass

    formatted_data = format_orders_for_table(recent_orders)
    
    in_work_count = len([o for o in ORDERS_DB['in_work'] if datetime.strptime(o['date'], '%d.%m.%y %H:%M').date() in [today, yesterday]])
    closed_count = len([o for o in ORDERS_DB['closed'] if datetime.strptime(o['date'], '%d.%m.%y %H:%M').date() in [today, yesterday]])

    return render_template_string(BASE_HTML, content=render_template_string(CHECKOUT_LIST_HTML, orders=formatted_data, status=status), current_tab='checkout', current_status=status, in_work_count=in_work_count, closed_count=closed_count, show_topbar=True, kassa=get_kassa_totals())

@app.route('/clients')
def clients():
    if 'user' not in session: return redirect(url_for('login'))
    
    clients_dict = {}
    for status in ['closed', 'in_work']:
        for o in ORDERS_DB[status]:
            phone = o.get('phone', '').strip()
            if not phone: phone = 'Без телефона'
            
            if phone not in clients_dict:
                clients_dict[phone] = {
                    'phone': phone,
                    'name': o.get('name', ''),
                    'mark': o.get('mark', ''),
                    'num': o.get('num', ''),
                    'total_amount': 0,
                    'orders': []
                }
            
            if not clients_dict[phone]['name'] and o.get('name'): clients_dict[phone]['name'] = o['name']
            if not clients_dict[phone]['mark'] and o.get('mark'): clients_dict[phone]['mark'] = o['mark']
            if not clients_dict[phone]['num'] and o.get('num') and o.get('num') != 'БН': clients_dict[phone]['num'] = o['num']

            amt = int(str(o.get('amount', '0')).replace(' ₽', '').replace(' ', ''))
            clients_dict[phone]['total_amount'] += amt
            
            base_grp = 'truck' if o.get('type_id') == 'truck' else 'car'
            srv_list = []
            for s_id, qty in o.get('services', {}).items():
                name = SRV_NAMES[base_grp].get(s_id, s_id)
                if base_grp == 'car' and o.get('radius'): name += f" {o['radius']}"
                if qty > 1: name += f" x {qty}"
                srv_list.append(name)
                
            clients_dict[phone]['orders'].append({
                'date': o.get('date', ''),
                'services': '<br>'.join(srv_list) or '—',
                'master': o.get('master', ''),
                'payment': o.get('payment_method', ''),
                'amount': f"{amt:,} ₽".replace(',', ' ')
            })
            
    client_list = list(clients_dict.values())
    client_list.sort(key=lambda x: x['total_amount'], reverse=True)
    
    return render_template_string(BASE_HTML, content=render_template_string(CLIENTS_HTML, clients=client_list), current_tab='clients', show_topbar=False, kassa=get_kassa_totals())

# НОВАЯ ВКЛАДКА РАСХОДЫ
@app.route('/expenses')
def expenses():
    if 'user' not in session: return redirect(url_for('login'))
    
    dates_param = request.args.get('dates')
    filtered_expenses = EXPENSES_DB.copy()
    
    if dates_param:
        try:
            start_str, end_str = dates_param.split(' - ')
            start_date = datetime.strptime(start_str.strip(), '%d.%m.%y')
            end_date = datetime.strptime(end_str.strip() + ' 23:59:59', '%d.%m.%y %H:%M:%S')
            
            f_list = []
            for e in filtered_expenses:
                try:
                    e_date = datetime.strptime(e['date'], '%d.%m.%y')
                    if start_date <= e_date <= end_date:
                        f_list.append(e)
                except: pass
            filtered_expenses = f_list
        except: pass

    # Подсчет итогов для отображения (если нужно)
    return render_template_string(BASE_HTML, content=render_template_string(EXPENSES_HTML, expenses=filtered_expenses, selected_dates=dates_param), current_tab='expenses', show_topbar=False, kassa=get_kassa_totals())

@app.route('/api/save_expense', methods=['POST'])
def save_expense_api():
    if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    new_expense = {
        'id': str(uuid.uuid4())[:8],
        'date': data.get('date', ''),
        'desc': data.get('desc', 'Без описания'),
        'payment': data.get('payment', 'Наличные'),
        'deduct': data.get('deduct', True),
        'amount': int(data.get('amount', 0))
    }
    EXPENSES_DB.insert(0, new_expense)
    return jsonify({'status': 'success'})

@app.route('/api/delete_expense', methods=['POST'])
def delete_expense_api():
    if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    exp_id = request.json.get('id')
    global EXPENSES_DB
    EXPENSES_DB = [e for e in EXPENSES_DB if str(e.get('id')) != str(exp_id)]
    return jsonify({'status': 'success'})


@app.route('/create_order')
def create_order():
    if 'user' not in session: return redirect(url_for('login'))
    order_id = request.args.get('id')
    order_obj = next((o for lst in ORDERS_DB.values() for o in lst if str(o.get('id')) == str(order_id)), None)
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    in_work_count = len([o for o in ORDERS_DB['in_work'] if datetime.strptime(o['date'], '%d.%m.%y %H:%M').date() in [today, yesterday]])
    closed_count = len([o for o in ORDERS_DB['closed'] if datetime.strptime(o['date'], '%d.%m.%y %H:%M').date() in [today, yesterday]])

    return render_template_string(BASE_HTML, content=render_template_string(CREATE_ORDER_HTML, order=order_obj, prices_json=json.dumps(PRICES_DB), workers=WORKERS_DB, stock_json=json.dumps(STOCK_DB)), current_tab='checkout', current_status='in_work', in_work_count=in_work_count, closed_count=closed_count, show_topbar=True, kassa=get_kassa_totals())

@app.route('/api/save_order', methods=['POST'])
def save_order_api():
    if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    order_id = data.get('id')
    
    order_payload = {
        'date': data.get('date', ''), 'type': data.get('type', ''), 'type_id': data.get('type_id', 'car'),
        'radius': data.get('radius', 'R16'), 'num': data.get('num', ''), 'mark': data.get('mark', ''),
        'name': data.get('name', ''), 'phone': data.get('phone', ''), 'model': data.get('model', ''),
        'master': data.get('master', 'Не назначен'), 'payment_method': data.get('payment_method', 'Наличные'),
        'amount': data.get('amount', '0').replace(' ₽', '').replace(' ', ''),
        'discount': data.get('discount', 0), 'services': data.get('services', {}), 'stock': data.get('stock', {}),
        'per_service_workers': data.get('per_service_workers', {}), 'per_service_discounts': data.get('per_service_discounts', {}),
        'status': 'in_work'
    }
    
    if order_id:
        for status_list in [ORDERS_DB['in_work'], ORDERS_DB['closed']]:
            for o in status_list:
                if str(o.get('id')) == str(order_id):
                    order_payload['status'] = o.get('status', 'in_work')
                    o.update(order_payload)
                    return jsonify({'status': 'success'})

    order_payload['id'] = str(uuid.uuid4())[:8]
    ORDERS_DB['in_work'].insert(0, order_payload)
    return jsonify({'status': 'success'})

@app.route('/api/delete_order', methods=['POST'])
def delete_order_api():
    if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    order_id = request.json.get('id')
    for key in ['in_work', 'closed']:
        ORDERS_DB[key] = [o for o in ORDERS_DB[key] if str(o.get('id')) != str(order_id)]
    return jsonify({'status': 'success'})



if __name__ == '__main__':
    print("Сервер запущен! Откройте в браузере http://127.0.0.1:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
