from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime, date

app = Flask(__name__)
DB = 'expenses.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT, category TEXT, description TEXT, amount REAL)''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/expenses', methods=['GET', 'POST'])
def expenses():
    conn = get_db()
    if request.method == 'POST':
        data = request.get_json()
        date_val = data['date']
        category = data['category']
        description = data.get('description', '')
        amount = float(data['amount'])
        conn.execute(
            'INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)',
            (date_val, category, description, amount)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True})

    # GET: filter by day, month, or year
    day = request.args.get('date')      # YYYY-MM-DD
    month = request.args.get('month')   # YYYY-MM
    year = request.args.get('year')     # YYYY

    if day:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE date = ? ORDER BY id DESC", (day,)
        ).fetchall()
        # Category totals for that day
        category_rows = conn.execute(
            "SELECT category, SUM(amount) as total FROM expenses WHERE date = ? GROUP BY category",
            (day,)
        ).fetchall()
    elif month:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE strftime('%Y-%m', date) = ? ORDER BY date DESC, id DESC",
            (month,)
        ).fetchall()
        category_rows = conn.execute(
            "SELECT category, SUM(amount) as total FROM expenses WHERE strftime('%Y-%m', date) = ? GROUP BY category",
            (month,)
        ).fetchall()
    elif year:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE strftime('%Y', date) = ? ORDER BY date DESC, id DESC",
            (year,)
        ).fetchall()
        category_rows = conn.execute(
            "SELECT category, SUM(amount) as total FROM expenses WHERE strftime('%Y', date) = ? GROUP BY category",
            (year,)
        ).fetchall()
    else:
        # Default to today
        today_str = date.today().isoformat()
        rows = conn.execute(
            "SELECT * FROM expenses WHERE date = ? ORDER BY id DESC", (today_str,)
        ).fetchall()
        category_rows = conn.execute(
            "SELECT category, SUM(amount) as total FROM expenses WHERE date = ? GROUP BY category",
            (today_str,)
        ).fetchall()

    conn.close()

    expenses_list = [dict(r) for r in rows]
    category_totals = [{'category': r['category'], 'total': r['total']} for r in category_rows]
    total_spent = sum(r['amount'] for r in rows)

    return jsonify({
        'expenses': expenses_list,
        'category_totals': category_totals,
        'total_spent': total_spent
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)