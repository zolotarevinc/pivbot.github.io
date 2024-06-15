import logging
from aiohttp import web
import aiohttp_jinja2
import jinja2
from database import SessionLocal, get_user, update_balance, get_top_users, create_user
import os
import asyncio


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

routes = web.RouteTableDef()


@routes.get('/')
async def index(request):
    '''функция запуска веб приложения'''
    try:
        user_id = request.query.get('user_id')
        if not user_id:
            raise web.HTTPBadRequest(reason="Missing user_id parameter")

        db = SessionLocal()
        user = get_user(db, int(user_id))
        if not user:
            raise web.HTTPNotFound(reason="User not found")

        context = {
            'user_id': user_id,
            'balance': user.balance,
            'increment': user.increment
        }
        response = aiohttp_jinja2.render_template('index.html', request, context)
        return response
    except Exception as e:
        logger.error(f"Error in index handler: {e}", exc_info=True)
        return web.Response(text="Internal Server Error", status=500)


@routes.post('/increment')
async def increment(request):
    '''функция для добавления монет за тап'''
    try:
        data = await request.json()
        user_id = int(data['user_id'])

        db = SessionLocal()
        user = get_user(db, user_id)
        if user:
            user.balance += user.increment
            db.commit()
            db.refresh(user)

        return web.json_response({'balance': user.balance})
    except Exception as e:
        logger.error(f"Error in increment handler: {e}", exc_info=True)
        return web.Response(text="Internal Server Error", status=500)


@routes.get('/leaderboard')
async def leaderboard(request):
    '''функция для открытия страницы с топом'''
    try:
        user_id = request.query.get('user_id')
        if not user_id:
            raise web.HTTPBadRequest(reason="Missing user_id parameter")

        db = SessionLocal()
        user = get_user(db, int(user_id))
        if not user:
            raise web.HTTPNotFound(reason="User not found")

        top_users = get_top_users(db)
        top_users_with_username = [{'username': get_user(db, user.id).username, 'balance': user.balance} for user
                                   in top_users]

        context = {
            'user_id': user_id,
            'top_users': top_users_with_username
        }
        response = aiohttp_jinja2.render_template('leaderboard.html', request, context)
        return response
    except Exception as e:
        logger.error(f"Error in leaderboard handler: {e}", exc_info=True)
        return web.Response(text="Internal Server Error", status=500)


@routes.get('/store')
async def store(request):
    '''функция для открытия магазина'''
    try:
        user_id = request.query.get('user_id')
        if not user_id:
            raise web.HTTPBadRequest(reason="Missing user_id parameter")

        db = SessionLocal()
        user = get_user(db, int(user_id))
        if not user:
            raise web.HTTPNotFound(reason="User not found")

        context = {
            'user_id': user_id,
            'balance': user.balance
        }
        response = aiohttp_jinja2.render_template('store.html', request, context)
        return response
    except Exception as e:
        logger.error(f"Error in store handler: {e}", exc_info=True)
        return web.Response(text="Internal Server Error", status=500)


async def automatic_coin_increase(user_id: int):
    '''функция для начисления +1 каждые 2 секунды (как оно работает - только бог знает)'''
    db = SessionLocal()
    user = get_user(db, user_id)
    if user:
        while True:
            await asyncio.sleep(2)  # Подождать 2 секунды
            user = get_user(db, user_id)
            if user:
                db = SessionLocal()
                user = get_user(db, user_id)
                user.balance += 1
                db.commit()
                db.refresh(user)

# Использование этой функции при покупке соответствующего товара:
# В обработчике POST /buy, где item_id == 2


@routes.post('/buy')
async def buy(request):
    '''функция для покупки товаров id=1: +5 за тап // id=2: +1 монета каждые 2 секунды'''
    try:
        data = await request.json()
        user_id = int(data['user_id'])
        item_id = int(data['item_id'])

        db = SessionLocal()
        user = get_user(db, user_id)
        if not user:
            raise web.HTTPNotFound(reason="User not found")

        if item_id == 1 and user.balance >= 500:
            user.balance -= 500
            user.increment += 5
        elif item_id == 2 and user.balance >= 1000:
            user.balance -= 1000
            asyncio.create_task(automatic_coin_increase(user_id))  # Запуск автоматического начисления монет
        else:
            return web.Response(text="Not enough balance or invalid item", status=400)

        db.commit()
        db.refresh(user)
        return web.json_response({'balance': user.balance})
    except Exception as e:
        logger.error(f"Error in buy handler: {e}", exc_info=True)
        return web.Response(text="Internal Server Error", status=500)


app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))
app.add_routes(routes)

# Добавление маршрута для обслуживания статических файлов
static_dir = os.path.join(os.path.dirname(__file__), 'static')
app.router.add_static('/static/', static_dir)

if __name__ == '__main__':
    web.run_app(app, port=8080)







