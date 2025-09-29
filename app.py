from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, session

app = Flask(__name__)
# 보안을 위해 실제 환경에서는 강력하고 복잡한 SECRET_KEY를 사용해야 합니다.
app.config['SECRET_KEY'] = 'your_very_secret_and_complex_key_here' 

VALID_INVITE_CODE = '12345678'
USER_NAME_COOKIE = 'newbie_name' # 사용자 이름을 저장할 쿠키 이름

# 🔑 관리자 인증 정보 (실제 환경에서는 DB 및 해시 사용)
ADMIN_USER = 'admin'
ADMIN_PASS = 'secure1234' 
ADMIN_SESSION_KEY = 'is_admin'

# 🚨 임시 사용자별 데이터 저장소 (실제로는 DB를 사용해야 합니다)
# 구조: {'사용자 이름': {'checklist': {'item1': True, 'item2': False, ...}}}
user_data_store = {}

# ☎️ 전화번호부 데이터 수정: 'position' 항목 추가
CONTACTS = [
    {'name': '인사팀 담당자', 'position': '인사 및 복리후생', 'number': '02-1234-5678'},
    {'name': 'IT 지원팀 (장비 문의)', 'position': '기술 지원 및 장비 관리', 'number': '02-9876-5432'},
    {'name': '팀장님 (김민수)', 'position': '신입팀 리더', 'number': '010-1111-2222'},
    {'name': '총무팀 (사무용품)', 'position': '자산 및 사무용품 관리', 'number': '02-5555-4444'}
]

# === 체크리스트 데이터 구조 변경: 'description' 추가 ===
def get_initial_checklist():
    return {
        '회사 소개 자료 검토': {
            'checked': False,
            'description': '회사의 비전, 문화, 주요 사업에 대한 소개 자료를 읽고 숙지합니다.'
        },
        '인사팀 오리엔테이션 완료': {
            'checked': False,
            'description': '급여, 복리후생, 사내 규정에 대한 인사팀 교육에 참석합니다.'
        },
        '개발 환경 (IDE) 설정 완료': {
            'checked': False,
            'description': '개인 컴퓨터에 필요한 소프트웨어와 개발 도구를 모두 설치하고 정상 동작을 확인합니다.'
        },
        '팀원들과 점심 식사': {
            'checked': False,
            'description': '팀에 자연스럽게 적응하기 위해 팀원들과 함께 점심 식사를 하며 소통합니다.'
        },
        '보안 서약서 제출': {
            'checked': False,
            'description': '회사 정보 보호를 위한 보안 서약서를 작성하여 인사팀에 제출합니다.'
        }
    }

# 메인 페이지 라우트
@app.route('/')
def index():
    user_name = request.cookies.get(USER_NAME_COOKIE)
    if user_name:
        return redirect(url_for('welcome', name=user_name))
    return render_template('main.html')

# 초대 코드 또는 이름 제출 처리 라우트 (POST)
@app.route('/join', methods=['POST'])
def join():
    input_key = request.form.get('invite_code').strip()
    if input_key == VALID_INVITE_CODE:
        return redirect(url_for('register'))
    if input_key in user_data_store:
        response = make_response(redirect(url_for('dashboard')))
        response.set_cookie(USER_NAME_COOKIE, input_key, max_age=60*60*24*30) 
        return response
    return redirect(url_for('index'))

# 사용자 등록 페이지
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.cookies.get(USER_NAME_COOKIE):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        user_name = request.form.get('user_name').strip()
        if user_name:
            if user_name not in user_data_store:
                 user_data_store[user_name] = {
                    'checklist': get_initial_checklist() # 수정된 데이터 구조 사용
                }
            
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie(USER_NAME_COOKIE, user_name, max_age=60*60*24*30) 
            return response
        else:
            return render_template('register.html', error="이름을 입력해 주세요.")
    return render_template('register.html', error=None)

# 사용자 대시보드
@app.route('/dashboard')
def dashboard():
    user_name = request.cookies.get(USER_NAME_COOKIE)
    if not user_name:
        return redirect(url_for('index'))

    checklist_items = user_data_store.get(user_name, {}).get('checklist', {})

    faq_items = [
        {'title': '인턴 기간은 얼마나 되나요?', 'content': '정규직 전환을 염두에 둔 인턴 기간은 3개월입니다. 이후 내부 평가를 통해 정규직 전환 여부가 결정됩니다.'},
        {'title': '복리후생 관련 문의는 어디로 해야 하나요?', 'content': '복리후생(휴가, 급여, 보험 등)에 대한 자세한 문의는 인사팀 이메일 (hr@company.com) 또는 내선 123번으로 연락 주십시오.'},
        {'title': '사내 헬스장 이용 방법은요?', 'content': '사내 헬스장은 신입 오리엔테이션 시 발급받은 사원증으로 자유롭게 이용 가능하며, 개인 락커는 총무팀에 신청해야 합니다.'}
    ]
    
    return render_template('dashboard.html', 
                           name=user_name,
                           checklist=checklist_items,
                           faq=faq_items)

# 로그아웃
@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('index')))
    response.set_cookie(USER_NAME_COOKIE, '', expires=0) 
    return response

# 체크리스트 상태 업데이트 API
@app.route('/update_checklist', methods=['POST'])
def update_checklist():
    user_name = request.cookies.get(USER_NAME_COOKIE)
    if not user_name:
        return jsonify({'success': False, 'message': '로그인 정보가 없습니다.'}), 401 

    data = request.get_json()
    item_key = data.get('item_key')
    is_checked = data.get('is_checked')

    if user_name in user_data_store and item_key in user_data_store[user_name]['checklist']:
        user_data_store[user_name]['checklist'][item_key]['checked'] = is_checked # 수정된 데이터 구조에 맞게 업데이트
        print(f"[{user_name}] 체크리스트 업데이트: {item_key} -> {is_checked}")
        return jsonify({'success': True, 'item': item_key, 'checked': is_checked})
    
    return jsonify({'success': False, 'message': '잘못된 항목입니다.'}), 400

# 전화번호부 페이지
@app.route('/contacts')
def contacts():
    if not request.cookies.get(USER_NAME_COOKIE):
        return redirect(url_for('index'))
    return render_template('contacts.html', contacts=CONTACTS)

# 웰컴 페이지 (바로 대시보드로 리다이렉트)
@app.route('/welcome')
def welcome():
    user_name = request.args.get('name') or request.cookies.get(USER_NAME_COOKIE)
    if not user_name:
        return redirect(url_for('index'))
    return redirect(url_for('dashboard'))

# --- 관리자 기능 ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if session.get(ADMIN_SESSION_KEY):
        return redirect(url_for('view_admin_dashboard'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USER and password == ADMIN_PASS:
            session[ADMIN_SESSION_KEY] = True
            return redirect(url_for('view_admin_dashboard'))
        else:
            error = "사용자 이름 또는 비밀번호가 올바르지 않습니다."
    return render_template('admin_login.html', error=error)

@app.route('/admin_dashboard')
def view_admin_dashboard():
    if not session.get(ADMIN_SESSION_KEY):
        return redirect(url_for('admin_login'))

    # 데이터 가공 로직 (수정된 데이터 구조에 맞게 조정)
    user_names = list(user_data_store.keys())
    
    if not user_names:
        checklist_keys = []
        status_map = {}
    else:
        # 첫 번째 사용자의 체크리스트 키를 기준으로 삼음
        checklist_keys = list(user_data_store[user_names[0]]['checklist'].keys())
        status_map = {
            name: {key: data['checklist'][key]['checked'] for key in checklist_keys}
            for name, data in user_data_store.items()
        }
        
    return render_template('admin.html', 
                           user_names=user_names,
                           checklist_keys=checklist_keys,
                           status_map=status_map)

@app.route('/admin_logout')
def admin_logout():
    session.pop(ADMIN_SESSION_KEY, None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
