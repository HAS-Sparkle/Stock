from fastapi import FastAPI, Request, Response
from starlette.background import BackgroundTask
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.types import Message
from module.csv_utils import get_current_price, get_history, get_all, get_max
from pydantic import BaseModel
import pymysql
import time
import logging

app = FastAPI()


starttime = time.time()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "???????",
    "database": "sparklestock"
}

class LoginData(BaseModel):
    id: str
    pw: str

class DealData(BaseModel):
    id: str
    pw: str
    amount: str


logging.basicConfig(filename='info.log', level=logging.INFO)


def log_info(req_body, client_ip, method, url, status_code):
    """
    로그 정보를 기록하는 함수
    """
    logging.info(f"Client IP: {client_ip}, Method: {method}, URL: {url}, Request Body: {req_body}, Status Code: {status_code}")


# not needed when using FastAPI>=0.108.0.
async def set_body(request: Request, body: bytes):
    """
    요청 본문(body)을 설정하는 함수
    """
    async def receive() -> Message:
        return {'type': 'http.request', 'body': body}

    request._receive = receive


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    미들웨어 클래스로 모든 예외를 캐치하고 로깅하는 역할 수행
    """
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # 클라이언트 IP, 요청 메서드, URL 정보 추출
            client_ip = request.client.host
            method = request.method
            url = request.url.path

            # 예외 정보 로깅
            logging.exception(f"Exception occurred for Client IP: {client_ip}, Method: {method}, URL: {url}")

            # 예외를 다시 발생시킴
            raise e


@app.middleware('http')
async def some_middleware(request: Request, call_next):
    """
    미들웨어 함수로 요청과 응답 정보를 로깅하는 함수
    """
    req_body = await request.body()
    await set_body(request, req_body)  # not needed when using FastAPI>=0.108.0.

    # 클라이언트 IP, 요청 메서드, URL 정보 추출
    client_ip = request.client.host
    method = request.method
    url = request.url.path

    response = await call_next(request)

    # 응답 본문(body) 및 상태 코드 추출
    res_body = b''
    async for chunk in response.body_iterator:
        res_body += chunk
    status_code = response.status_code

    # 로그 정보를 백그라운드 태스크로 실행
    task = BackgroundTask(log_info, req_body.decode('utf-8'), client_ip, method, url, status_code)

    # 응답 반환
    return Response(content=res_body, status_code=status_code,
                    headers=dict(response.headers), media_type=response.media_type, background=task)

# 에러를 처리하기 위한 미들웨어 등록
app.add_middleware(ErrorLoggingMiddleware)


@app.post("/api/login")
async def root(userInfo:LoginData):
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    query = f'SELECT * FROM users WHERE id="{userInfo.id}"'
    cursor.execute(query)

    if len(cursor.fetchall()) != 0: #로그인 기록 있음
        query = f'SELECT * FROM users WHERE id="{userInfo.id}"'
        cursor.execute(query)
        if cursor.fetchall()[0][1] != userInfo.pw:
            return False
            connection.close()
        connection.close()
        return True

    else: #처음 로그인
        query = f'INSERT INTO users VALUES ("{userInfo.id}", "{userInfo.pw}", "1000000", "0")'
        cursor.execute(query)
        connection.commit()
        connection.close()
        return True

@app.get("/api/getprice")
async def root():
    global starttime
    current_time = time.time()
    difference = round(current_time - starttime)
    if round(difference//1)+1 > 3682:
        return "close"
    price = get_current_price(difference)
    return float(price)

@app.get("/api/gethistory")
async def root():
    global starttime
    current_time = time.time()
    difference = round(current_time - starttime)

    if round(difference // 1) + 1 > 3682:
        return get_all()
    return get_history(difference)


@app.post("/api/buy")
async def root(userInfo:DealData):
    global starttime
    if int(float(userInfo.amount)) < 0 : return "수량은 0보다 작을 수 없습니다."

    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    query = f'SELECT * FROM users WHERE id="{userInfo.id}"'
    cursor.execute(query)

    if len(cursor.fetchall()) != 0:  # 로그인 기록 있음
        query = f'SELECT * FROM users WHERE id="{userInfo.id}"'
        cursor.execute(query)
        account = cursor.fetchall()[0]

        if account[1] != userInfo.pw:
            return "비밀번호가 잘못되었습니다."
            connection.close()

        current_time = time.time()
        difference = round(current_time - starttime)
        if round(difference // 1) + 1 > 3682: price = get_max()
        else: price = get_current_price(difference)
        if int(account[2]) >= int(float(userInfo.amount))*price:
            query = f'UPDATE users SET money = "{round(int(account[2])-int(float(userInfo.amount))*price)}" WHERE id="{userInfo.id}"'
            cursor.execute(query)
            connection.commit()
            query = f'UPDATE users SET stock = "{int(account[3])+int(float(userInfo.amount))}" WHERE id="{userInfo.id}"'
            cursor.execute(query)
            connection.commit()
            connection.close()
            return True
        else:
            return "매수량이 가진 현금을 초과했습니다."

    else:  # 처음 로그인
        return "존재하지 않는 계정입니다."

@app.post("/api/sell")
async def root(userInfo:DealData):
    global starttime
    if int(float(userInfo.amount)) < 0 : return "수량은 0보다 작을 수 없습니다."

    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    query = f'SELECT * FROM users WHERE id="{userInfo.id}"'
    cursor.execute(query)

    if len(cursor.fetchall()) != 0:  # 로그인 기록 있음
        query = f'SELECT * FROM users WHERE id="{userInfo.id}"'
        cursor.execute(query)
        account = cursor.fetchall()[0]

        if account[1] != userInfo.pw:
            return "비밀번호가 잘못되었습니다."
            connection.close()

        current_time = time.time()
        difference = round(current_time - starttime)
        if round(difference // 1) + 1 > 3682: price = get_max()
        else: price = get_current_price(difference)
        if int(account[3]) >= int(float(userInfo.amount)):
            query = f'UPDATE users SET money = "{round(int(account[2])+int(float(userInfo.amount))*price)}" WHERE id="{userInfo.id}"'
            cursor.execute(query)
            connection.commit()
            query = f'UPDATE users SET stock = "{int(account[3])-int(float(userInfo.amount))}" WHERE id="{userInfo.id}"'
            cursor.execute(query)
            connection.commit()
            connection.close()
            return True
        else:
            return "매도량이 가진 주식 수를 초과하였습니다."

    else:  # 처음 로그인
        return "존재하지 않는 계정입니다."

@app.post("/api/check")
async def root(userInfo:LoginData):
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    query = f'SELECT * FROM users WHERE id="{userInfo.id}"'
    cursor.execute(query)

    if len(cursor.fetchall()) != 0:  # 로그인 기록 있음
        query = f'SELECT * FROM users WHERE id="{userInfo.id}"'
        cursor.execute(query)
        account = cursor.fetchall()[0]
        connection.close()
        if account[1] != userInfo.pw:
            return "비밀번호가 잘못되었습니다."

        return {"money": account[2], "stock": account[3]}

    else:  # 처음 로그인
        return "존재하지 않는 계정입니다."

@app.get("/api/leaderboard")
async def root():
    global starttime
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    query = f'SELECT * FROM users'
    cursor.execute(query)
    users = cursor.fetchall()
    current_time = time.time()
    difference = round(current_time - starttime)
    if round(difference // 1) + 1 > 3682: price = get_max()
    else: price = get_current_price(difference)
    leaderboard = [{"id":i[0], "money":round(int(i[2])+int(i[3])*price)} for i in users]
    sorted_leaderboard = sorted(leaderboard, key=lambda x: x['money'], reverse=True)
    return sorted_leaderboard