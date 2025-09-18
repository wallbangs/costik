from aiogram import F, Router, types, Bot
from aiogram.filters.command import CommandStart
from aiogram.filters import Command
from keyboards.admin import admin_command
from database.db import DataBase
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID, VERIF_CHANNEL_ID
class Admin_States(StatesGroup):
    #give balance(выдача баланса)
    
    get_userinfo = State()
    give_balance = State()
    
    #delete balance(удаление баланса)

    get_userinfo_del = State()
    delete_balance = State()

    #mailing(рассылка)

    mailing_text = State()
    
    #change referral
    input_ref = State()
    
    #user management
    demote_user_id = State()
    reset_user_id = State()


router = Router()


@router.message(F.from_user.id == ADMIN_ID, Command("admin"))
async def admin_panel(message: types.Message):
    await message.answer("Админ панель", reply_markup=await admin_command())



@router.message(F.text == '/admin')
async def admin_handler(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await state.clear()
        users_count = await DataBase.get_users()
        money_list = await DataBase.get_users()
        money_count = 0
        await message.answer("Добро пожаловать", reply_markup=await admin_command(), parse_mode="HTML")
    else:
        await message.answer("Команда доступна только администраторам бота!",parse_mode="HTML")


@router.callback_query(F.data == 'stat')
async def statistics_handler(callback: types.CallbackQuery):
    users_count = await DataBase.get_users_count()
    verified_count = await DataBase.get_verified_users_count()
    statistics_message = (
        f"<b>Статистика бота:</b>\n"
        f"🔹 <b>Общее количество пользователей:</b> <code>{users_count}</code>\n"
        f"🔹 <b>Количество пользователей прошедших верификацию:</b> <code>{verified_count}</code>"
    )
    await callback.message.answer(statistics_message, parse_mode="HTML")


@router.callback_query(F.data == 'mailing')
async def mailing_state(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer("Отправьте сообщение")
    await state.set_state(Admin_States.mailing_text)


@router.message(Admin_States.mailing_text)
async def mailing_state(message: types.Message, state: FSMContext, bot: Bot):
    mailing_message = message.message_id
    ikb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text='Отправить', callback_data='send_mailing'), types.InlineKeyboardButton(
            text='Отмена', callback_data='decline_mailing')]
    ])
    await bot.copy_message(chat_id=message.chat.id, from_chat_id=message.chat.id,
                           message_id=mailing_message, reply_markup=ikb, parse_mode="HTML")

    await state.update_data(msg=mailing_message)


@router.callback_query(F.data == 'send_mailing')
async def mailing_handler(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    errors_count = 0
    good_count = 0
    data = await state.get_data()
    mailing_message = data['msg']
    users = await DataBase.get_users()
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer("Рассылка начата...")
    for i in users:
        try:
            await bot.copy_message(chat_id=i[1], from_chat_id=callback.from_user.id,
                                   message_id=mailing_message, parse_mode="HTML")
            good_count += 1
        except Exception as ex:
            errors_count += 1
            print(ex)

    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(f"<b>Кол-во отосланных сообщений:</b> <code>{good_count}</code>\n\
<b>Кол-во пользователей заблокировавших бота:</b> <code>{errors_count}</code>", parse_mode="HTML")
    await callback.answer()
    await state.clear()


@router.callback_query(F.data == 'decline_mailing')
async def decline_mailing(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer("Рассылка отменена", reply_markup=await admin_command())
    await state.clear()


@router.callback_query(F.data == 'verificate')
async def verificate_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer("Отправьте ID пользователя для верификации:")
    await state.set_state(Admin_States.get_userinfo)


@router.message(Admin_States.get_userinfo)
async def get_user_for_verification(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        user_info = await DataBase.get_user_info(user_id)
        if user_info:
            await DataBase.set_verification(user_id)
            await message.answer(f"Пользователь {user_id} успешно верифицирован!", reply_markup=await admin_command())
        else:
            await message.answer("Пользователь не найден в базе данных!", reply_markup=await admin_command())
    except ValueError:
        await message.answer("Неверный формат ID пользователя!", reply_markup=await admin_command())
    await state.clear()


@router.callback_query(F.data == "change_ref")
async def change_referral_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id == ADMIN_ID:
        try:
            await callback.message.delete()
        except:
            pass
        await callback.message.answer("Введите новую реферальную ссылку:")
        await state.set_state(Admin_States.input_ref)
    else:
        await callback.answer("Доступно только администраторам!", show_alert=True)


@router.message(Admin_States.input_ref)
async def change_referral_message_state(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Реферальная ссылка изменена!", reply_markup=await admin_command())
        await DataBase.edit_ref(message.text)
    await state.clear()


@router.callback_query(F.data == 'demote_user')
async def demote_user_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer("Отправьте ID пользователя для сброса до незарегистрированного:")
    await state.set_state(Admin_States.demote_user_id)


@router.message(Admin_States.demote_user_id)
async def demote_user_by_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        user_info = await DataBase.get_user_info(user_id)
        if user_info:
            # Reset user to unregistered state
            await DataBase.set_verification(user_id, "unreg")
            await DataBase.update_deposit_status(user_id, "nedep")
            
            # Send notification to user that they've been demoted
            try:
                lang = await DataBase.get_lang(user_id)
                if lang:
                    await message.bot.send_message(
                        chat_id=user_id,
                        text="⚠️ Ваш статус был сброшен администратором. Пожалуйста, пройдите регистрацию заново."
                    )
            except Exception as e:
                print(f"Could not notify user {user_id}: {e}")
            
            await message.answer(f"Пользователь {user_id} сброшен до незарегистрированного состояния!", reply_markup=await admin_command())
        else:
            await message.answer("Пользователь не найден в базе данных!", reply_markup=await admin_command())
    except ValueError:
        await message.answer("Неверный формат ID пользователя!", reply_markup=await admin_command())
    await state.clear()


@router.callback_query(F.data == 'reset_user')
async def reset_user_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer("Отправьте ID пользователя для полного удаления из базы:")
    await state.set_state(Admin_States.reset_user_id)


@router.message(Admin_States.reset_user_id)
async def reset_user_by_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        user_info = await DataBase.get_user_info(user_id)
        if user_info:
            # Delete user completely from database
            await DataBase.delete_user(user_id)
            
            # Send notification to user that they've been removed
            try:
                lang = await DataBase.get_lang(user_id)
                if lang:
                    await message.bot.send_message(
                        chat_id=user_id,
                        text="⚠️ Ваш аккаунт был удален администратором. Для доступа к боту необходимо начать заново с команды /start"
                    )
            except Exception as e:
                print(f"Could not notify user {user_id}: {e}")
            
            await message.answer(f"Пользователь {user_id} полностью удален из базы данных!", reply_markup=await admin_command())
        else:
            await message.answer("Пользователь не найден в базе данных!", reply_markup=await admin_command())
    except ValueError:
        await message.answer("Неверный формат ID пользователя!", reply_markup=await admin_command())
    await state.clear()