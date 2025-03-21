from flask import Flask, request, jsonify, render_template, send_file
import sqlite3
import os
import glob
import time
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from urllib.parse import parse_qs
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
app = Flask(__name__, template_folder=TEMPLATE_DIR)

DB_PATH = os.path.join(BASE_DIR, "factory_accounts.db")

INITIAL_EXPENSE_TYPES = [
    "مرتب وائل السواق", "مرتب عربية الماي", "مرتب عربية بخاتى", "مرتب عربية شبرا باص", "شحن", "ايجار القص والمخازن",
    "مرتب عربية قويسنا", "مرتب الامن", "شحن كارت كهرباء", "مرتب منى H.R", "قسط شهرى ا/أحمد الدسوقى", "برنتات تامينات",
    "تامينات الخط الرابع", "اجمالى مصروفات شهر 6", "اجمالى مصروفات شهر 7", "اجمالى مصروفات شهر 8", "مرتب السواقين",
    "عشاء وفطار", "مرتب الشواكين", "ايجار المصنع على 3", "ايجار الدور الرابع", "سلفه هانى سعيد", "مرتب اسماء شوقى",
    "سلفه اشرف امين", "صيانه طابعه", "صندوق الشكاوي", "ميزانيه للتيكت", "بادا كمبيوتر القص", "شحن بطاريات",
    "أيام شغل احمد عصام", "كارتات عربيات الكراتين", "كارته عربية صغيرة", "صيانه وقطع غيار", "سلفه امينه إبراهيم",
    "مرتب شيماء 5%", "اكرامية الزبالة", "تامينات الدور الرابع", "مرتب غفير", "شحن عينات", "ابر + صيانة الدور الرابع",
    "شحن بطاريه الديزل", "مرتبات المصنع", "فطار و سحور", "سلفه شهد كيلانى", "فرشة والوان لدهان الارض", "ايام شغل كريم الشال",
    "تصوير ورق لمدام منى واستمارات", "تامينات المصنع", "شحن شريط", "بياتات", "سلفه هالة سعيد", "مرتب خالد فايز 5%",
    "مقابض وافيز", "نقاش", "استمارات 111", "صاج لعربية القص", "فايبر للعينات", "اجره عربيه هاله للقماش", "اللوان وبرايمر",
    "سلفة محمود حمدى", "سلفة شريف حمدى", "مخالفه ارتفاع", "تامينات", "صيانه ميزان", "تحويل ماكينات الاستيك",
    "مرتب اميرة علاء باترون", "سلفه سمير عبد العظيم", "سلفة احمد على تركيب وصلة نت", "خشب للترابيزه", "صيانه الديزل",
    "للحداد", "باقي حساب الخيط شيك", "سباك", "ليد احمد نبيل", "صيانة مكواه", "صيانة الخط", "صيانة القص", "عصير وكنز",
    "غداء للضيوف", "سلفة منار ايمن", "سلفة يوسف السواق", "سلفة كريم نشات", "صيانة الدور الرابع + ابر", "نت القص",
    "فزلين", "فرق مرتب حنان السيد", "تنر", "سلفة نبوى حامد", "سلفة اسماء هانى", "دفعة يوسف السواق", "اكراميه رجالة يوسف",
    "اشراك طلبة مدارس اونست وسمارت", "سلك وخشب للشبابيك", "ضرائب عصام", "مني مقصات", "ايام شغل عبدالحميد صبحي",
    "ايام شغل محمد صبحى", "سلفه ولاء فهمي", "صيانه حمام", "ادوات نظافة للحمامات", "لمبات للقص", "مياه على 3", "مياه للقص",
    "مواصلات منى", "سلفه سجده ايمن", "سلفه ام احمد", "سلفه ايات بشير", "برايمر لحديد الترابيزات", "سن مقصات للقص",
    "باقى مرتب منى", "سن مقصات", "زيت للكمبروسر", "حساب عبدالرحمن الكهربائي", "حساب الحداد", "حساب صبيح استك",
    "سلفه لمياء علاء", "لفنى الانذار", "شحن سيزر", "استمارات 111 وكعب عمل", "سلفه فاطمه عبدالخالق", "كبل كهربا للقص",
    "أدوات نظافه للحمامات", "غلطه في مرتب ليلي احمد", "اجره وصيانه باسم", "شحنه شريط وكرتون خيط", "حبر للطباعه",
    "سلفه حسام السخاوي", "اشتراك طلبه المدرسه", "اشتراك طلبة المدرسة اونست سمارت", "أيام شغل عبد الحميد صبحى",
    "نقل كراتين احمد عباس", "سباكه للقص", "اكياس للمخزن", "خيوط", "سباكه حمام", "لزق 7 سم", "سلفه صفاء عيد",
    "شاش قطف بتادين ومناديل وصابون للحمامات", "تصليح عجلة القص", "تصليح الطباعه للقص", "سلفه مدام شادية",
    "ورق للطبعة", "سلفه شهد كلاني", "دخان السواق", "ادوات سباكه", "سلفة حنان السيد", "كارتات ليوسف",
    "شحن وتصليح بطارية ديزل", "اشتراك طلبة مدارس", "سلفة سحر محمود", "سلفة ايمان مصلحى", "سلفة امينة عبد الرحمن",
    "سلفه ساميه فتحى", "سلفة رقية عبد الحى", "سلفة فاطمة عبد الخالق", "تغير هاردات كاميرات"
]

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        type TEXT NOT NULL,
                        amount REAL NOT NULL
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS predictive_texts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        text TEXT NOT NULL UNIQUE
                    )''')

        c.execute("SELECT COUNT(*) FROM predictive_texts")
        if c.fetchone()[0] == 0:
            for text in INITIAL_EXPENSE_TYPES:
                c.execute("INSERT OR IGNORE INTO predictive_texts (text) VALUES (?)", (text,))

        conn.commit()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")

def cleanup_temp_files():
    temp_files = glob.glob(os.path.join(BASE_DIR, "tmp*.pdf"))
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
            print(f"Deleted old temporary file: {temp_file}")
        except Exception as e:
            print(f"Could not delete old temporary file {temp_file}: {e}")

def reshape_text(text):
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

@app.route('/')
def index():
    return render_template('indexx.html')

@app.route('/api/add_entry', methods=['POST'])
def add_entry():
    try:
        data = request.json
        date = data.get('date')  # يتوقع التاريخ بصيغة DD/MM/YYYY
        transaction_type = data.get('type')
        amount = float(data.get('amount', 0))
        expense_type = data.get('expense_type', '')

        if not date or not transaction_type or not amount:
            return jsonify({"error": "جميع الحقول مطلوبة"}), 400

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if transaction_type == "عهدة":
            c.execute("INSERT INTO accounts (date, type, amount) VALUES (?, ?, ?)", (date, "عهدة", amount))
        else:
            c.execute("INSERT INTO accounts (date, type, amount) VALUES (?, ?, ?)", (date, expense_type or "مصروفات", -amount))
        conn.commit()
        conn.close()
        return jsonify({"message": "تمت الإضافة بنجاح"})
    except ValueError:
        return jsonify({"error": "المبلغ يجب أن يكون رقمًا"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_data', methods=['GET'])
def get_data():
    try:
        month = request.args.get('month', '')
        year = request.args.get('year', '')
        type_filter = request.args.get('type', '')

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        query = "SELECT id, date, type, ABS(amount) as amount FROM accounts WHERE 1=1"
        params = []

        if month:
            query += " AND SUBSTR(date, 4, 2) = ?"  # استخراج الشهر من DD/MM/YYYY
            params.append(month)
        if year:
            query += " AND SUBSTR(date, 7, 4) = ?"  # استخراج السنة من DD/MM/YYYY
            params.append(year)
        if type_filter == "مصروفات":
            query += " AND type != ?"
            params.append("عهدة")
        elif type_filter == "عهدة":
            query += " AND type = ?"
            params.append("عهدة")

        query += " ORDER BY SUBSTR(date, 7, 4) || SUBSTR(date, 4, 2) || SUBSTR(date, 1, 2) DESC"
        c.execute(query, params)
        data = c.fetchall()
        conn.close()

        total_expenses = sum(row[3] for row in data if row[2] != "عهدة")
        total_advances = sum(row[3] for row in data if row[2] == "عهدة")

        return jsonify({
            "records": [{"id": row[0], "date": row[1], "type": row[2], "amount": row[3]} for row in data],
            "total_expenses": total_expenses,
            "total_advances": total_advances
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/update_entry', methods=['PUT'])
def update_entry():
    try:
        data = request.json
        entry_id = data.get('id')
        date = data.get('date')  # يتوقع التاريخ بصيغة DD/MM/YYYY
        transaction_type = data.get('type')
        amount = float(data.get('amount', 0))
        expense_type = data.get('expense_type', '')

        if not entry_id or not date or not transaction_type or not amount:
            return jsonify({"error": "جميع الحقول مطلوبة"}), 400

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if transaction_type == "عهدة":
            c.execute("UPDATE accounts SET date=?, type=?, amount=? WHERE id=?", (date, "عهدة", amount, entry_id))
        else:
            c.execute("UPDATE accounts SET date=?, type=?, amount=? WHERE id=?", (date, expense_type or "مصروفات", -amount, entry_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "تم التعديل بنجاح"})
    except ValueError:
        return jsonify({"error": "المبلغ يجب أن يكون رقمًا"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/delete_entry', methods=['DELETE'])
def delete_entry():
    try:
        entry_id = request.args.get('id')
        if not entry_id:
            return jsonify({"error": "معرف السجل مطلوب"}), 400

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM accounts WHERE id=?", (entry_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "تم الحذف بنجاح"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_pdf', methods=['GET'])
def generate_pdf():
    try:
        url = request.args.get('url', '/api/get_data')
        parsed_url = parse_qs(url.split('?')[1] if '?' in url else '')
        month = parsed_url.get('month', [''])[0]
        year = parsed_url.get('year', [''])[0]
        type_filter = parsed_url.get('type', [''])[0]

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        query = "SELECT id, date, type, ABS(amount) as amount FROM accounts WHERE 1=1"
        params = []

        if month:
            query += " AND SUBSTR(date, 4, 2) = ?"
            params.append(month)
        if year:
            query += " AND SUBSTR(date, 7, 4) = ?"
            params.append(year)
        if type_filter == "مصروفات":
            query += " AND type != ?"
            params.append("عهدة")
        elif type_filter == "عهدة":
            query += " AND type = ?"
            params.append("عهدة")

        query += " ORDER BY SUBSTR(date, 7, 4) || SUBSTR(date, 4, 2) || SUBSTR(date, 1, 2) DESC"
        c.execute(query, params)
        data = c.fetchall()
        conn.close()

        total_expenses = sum(row[3] for row in data if row[2] != "عهدة")
        total_advances = sum(row[3] for row in data if row[2] == "عهدة")

        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', dir=BASE_DIR)
        pdf_path = temp_pdf.name
        try:
            pdfmetrics.registerFont(TTFont('ArabicBold', os.path.join(BASE_DIR, 'arialbd.ttf')))
            c = canvas.Canvas(pdf_path, pagesize=A4)
            width, height = A4

            # العنوان
            c.setFont("ArabicBold", 20)
            c.setFillColor(colors.black)
            c.drawCentredString(width / 2, height - 30, reshape_text("تقرير مصروفات اونست"))

            # الإجماليات
            y = height - 50
            c.setFont("ArabicBold", 12)
            c.setFillColor(colors.black)
            c.drawCentredString(width / 4, y, reshape_text("إجمالي العهدة"))  # تصحيح "إجمالي العهده" إلى "إجمالي العهدة"
            c.setFillColor(colors.red)
            c.drawCentredString(width / 4 * 3, y, reshape_text(f"{total_advances:,} جنيه مصري"))

            y -= 20
            c.setFillColor(colors.black)
            c.drawCentredString(width / 4, y, reshape_text("إجمالي المصروفات"))
            c.setFillColor(colors.green)
            c.drawCentredString(width / 4 * 3, y, reshape_text(f"{total_expenses:,} جنيه مصري"))

            # جدول السجلات بعرض الصفحة الكامل
            y -= 30
            c.setFillColor(colors.lightgrey)
            c.rect(0, y - 20, width, 20, fill=1)
            c.setFillColor(colors.black)
            c.drawCentredString(width * 0.1, y - 15, reshape_text("الرقم"))
            c.drawCentredString(width * 0.3, y - 15, reshape_text("التاريخ"))
            c.drawCentredString(width * 0.6, y - 15, reshape_text("نوع المصروف"))
            c.drawCentredString(width * 0.9, y - 15, reshape_text("المبلغ"))
            c.setStrokeColor(colors.black)
            c.line(0, y, 0, y - 20)
            c.line(width * 0.2, y, width * 0.2, y - 20)
            c.line(width * 0.4, y, width * 0.4, y - 20)
            c.line(width * 0.8, y, width * 0.8, y - 20)
            c.line(width, y, width, y - 20)

            y -= 20
            for i, row in enumerate(data, 1):
                if y < 50:
                    c.showPage()
                    y = height - 50
                    c.setFont("ArabicBold", 12)
                    c.setFillColor(colors.lightgrey)
                    c.rect(0, y - 20, width, 20, fill=1)
                    c.setFillColor(colors.black)
                    c.drawCentredString(width * 0.1, y - 15, reshape_text("الرقم"))
                    c.drawCentredString(width * 0.3, y - 15, reshape_text("التاريخ"))
                    c.drawCentredString(width * 0.6, y - 15, reshape_text("نوع المصروف"))
                    c.drawCentredString(width * 0.9, y - 15, reshape_text("المبلغ"))
                    c.setStrokeColor(colors.black)
                    c.line(0, y, 0, y - 20)
                    c.line(width * 0.2, y, width * 0.2, y - 20)
                    c.line(width * 0.4, y, width * 0.4, y - 20)
                    c.line(width * 0.8, y, width * 0.8, y - 20)
                    c.line(width, y, width, y - 20)
                    y -= 20

                c.setFillColor(colors.black if row[2] != "عهدة" else colors.red)
                c.rect(0, y - 20, width, 20, stroke=1, fill=0)
                c.drawCentredString(width * 0.1, y - 15, str(i))
                c.drawCentredString(width * 0.3, y - 15, reshape_text(row[1]))
                c.drawCentredString(width * 0.6, y - 15, reshape_text(row[2]))
                c.drawCentredString(width * 0.9, y - 15, reshape_text(f"{row[3]:,} جنيه"))
                c.setStrokeColor(colors.black)
                c.line(0, y, 0, y - 20)
                c.line(width * 0.2, y, width * 0.2, y - 20)
                c.line(width * 0.4, y, width * 0.4, y - 20)
                c.line(width * 0.8, y, width * 0.8, y - 20)
                c.line(width, y, width, y - 20)
                y -= 20

            c.save()
        finally:
            temp_pdf.close()

        response = send_file(pdf_path, as_attachment=True, download_name="تقرير_مصروفات_اونست.pdf")

        time.sleep(2)
        try:
            os.remove(pdf_path)
            print(f"Deleted temporary file: {pdf_path}")
        except PermissionError:
            print(f"Could not delete {pdf_path}: File is in use.")
        except Exception as e:
            print(f"Error deleting {pdf_path}: {e}")

        return response
    except Exception as e:
        if 'pdf_path' in locals():
            try:
                os.remove(pdf_path)
            except:
                pass
        return jsonify({"error": str(e)}), 500

@app.route('/api/predictive_texts', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_predictive_texts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == 'GET':
        c.execute("SELECT text FROM predictive_texts")
        texts = [row[0] for row in c.fetchall()]
        conn.close()
        return jsonify(texts)

    elif request.method == 'POST':
        data = request.json
        text = data.get('text')
        if not text:
            conn.close()
            return jsonify({"error": "النص مطلوب"}), 400
        try:
            c.execute("INSERT INTO predictive_texts (text) VALUES (?)", (text,))
            conn.commit()
            conn.close()
            return jsonify({"message": "تمت الإضافة بنجاح"})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"error": "النص موجود مسبقًا"}), 400

    elif request.method == 'PUT':
        data = request.json
        old_text = data.get('old_text')
        new_text = data.get('new_text')
        if not old_text or not new_text:
            conn.close()
            return jsonify({"error": "النص القديم والجديد مطلوبان"}), 400
        c.execute("UPDATE predictive_texts SET text=? WHERE text=?", (new_text, old_text))
        if c.rowcount == 0:
            conn.close()
            return jsonify({"error": "النص غير موجود"}), 404
        conn.commit()
        conn.close()
        return jsonify({"message": "تم التعديل بنجاح"})

    elif request.method == 'DELETE':
        data = request.json
        text = data.get('text')
        if not text:
            conn.close()
            return jsonify({"error": "النص مطلوب"}), 400
        c.execute("DELETE FROM predictive_texts WHERE text=?", (text,))
        if c.rowcount == 0:
            conn.close()
            return jsonify({"error": "النص غير موجود"}), 404
        conn.commit()
        conn.close()
        return jsonify({"message": "تم الحذف بنجاح"})

# if __name__ == '__main__':
#     # Initialize the database and cleanup temporary files before running the app
#     cleanup_temp_files()
#     init_db()

#     # Run Flask only ONCE
#     app.run(debug=True, host="0.0.0.0", port=5000)