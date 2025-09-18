import asyncio
import datetime
from random import uniform, randint
#from main import bot, appFlask

from aiogram import F, Router, types, Bot
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from pprint import pprint

from database.db import DataBase
from keyboards.client import ClientKeyboard
from other.languages import languages
from config import CHANNEL_ID, CHANNEL_URL, BOT_TOKEN, VERIF_CHANNEL_ID
import aiohttp
class DummyUser:
    def __init__(self, user_id):
        self.id = user_id
class DummyCallback:
    def __init__(self, user_id):
        self.from_user = DummyUser(user_id)

router = Router()

class RegisterState(StatesGroup):
    input_id = State()

class GetSignalStates(StatesGroup):
    chosing_mines = State()



@router.message(CommandStart())
async def start_command(message: types.Message):
    await message.delete()
    lang = await DataBase.get_lang(message.chat.id)
    if lang is None:
        await get_language(message, True)
        return
    else:
        # Check channel subscription with actual verification on /start
        await check_channel_subscription_with_verification(message, lang)





async def check_channel_subscription_with_verification(message: types.Message, lang: str):
    # Check actual subscription status on /start
    subscription_status = await DataBase.get_subscription_status(message.from_user.id)
    
    if subscription_status == "yes":
        # Verify user is still subscribed
        try:
            member = await message.bot.get_chat_member(CHANNEL_ID, message.from_user.id)
            if member.status in ['member', 'administrator', 'creator']:
                await show_main_menu(message, lang)
                return
            else:
                # No longer subscribed, update database
                await DataBase.set_subscription_status(message.from_user.id, "no")
        except:
            # Can't check, assume unsubscribed
            await DataBase.set_subscription_status(message.from_user.id, "no")
    
    # User is not subscribed - show subscription prompt
    await message.answer(
        languages[lang]["welcome"].format(first_name=message.from_user.first_name),
        reply_markup=await ClientKeyboard.subscription_keyboard(lang, CHANNEL_URL),
        parse_mode="HTML"
    )

async def check_channel_subscription(message: types.Message, lang: str):
    # For language changes and other actions - just check database without verification
    subscription_status = await DataBase.get_subscription_status(message.from_user.id)
    
    if subscription_status == "yes":
        await show_main_menu(message, lang)
        return
    
    # User is not subscribed - show subscription prompt
    await message.answer(
        languages[lang]["welcome"].format(first_name=message.from_user.first_name),
        reply_markup=await ClientKeyboard.subscription_keyboard(lang, CHANNEL_URL),
        parse_mode="HTML"
    )

async def show_main_menu(message: types.Message, lang: str):
    # Force refresh user info from database to get latest state
    user_info = await DataBase.get_user_info(message.from_user.id)
    print(f"DEBUG: User {message.from_user.id} info: {user_info}")
    
    # Select photo based on language
    if lang == "ru":
        photo = types.FSInputFile("hello.jpg")
    elif lang == "ro":
        photo = types.FSInputFile("rohello.jpg")
    else:  # English
        photo = types.FSInputFile("hel.jpg")
    
    await message.answer_photo(
        photo, 
        caption=languages[lang]["welcome_message"],
        parse_mode="HTML",
        reply_markup=await ClientKeyboard.menu_keyboard(user_info, lang)
    )

@router.callback_query(F.data.startswith("sel_lang"))
async def select_language(callback: CallbackQuery):
    data = callback.data.split("|")
    await DataBase.register_lang(callback.from_user.id, data[2])
    # After language selection, check channel subscription
    lang = data[2]
    await check_channel_subscription(callback.message, lang)


@router.callback_query(F.data.startswith("resel_lang"))
async def reselect_language(callback: CallbackQuery):
    data = callback.data.split("|")
    print(f"DEBUG: Language change for user {data[1]} to {data[2]}")
    await DataBase.update_lang(int(data[1]), data[2])
    
    # After language change, go directly to main menu
    try:
        await callback.message.delete()
    except:
        pass
    
    lang = data[2]
    # Force refresh user info and show menu with updated language
    user_info = await DataBase.get_user_info(callback.from_user.id)
    print(f"DEBUG: User {callback.from_user.id} info after lang change: {user_info}")
    
    # Select photo based on language
    if lang == "ru":
        photo = types.FSInputFile("hello.jpg")
    elif lang == "ro":
        photo = types.FSInputFile("rohello.jpg")
    else:  # English
        photo = types.FSInputFile("hel.jpg")
    
    await callback.message.answer_photo(
        photo, 
        caption=languages[lang]["welcome_message"],
        parse_mode="HTML",
        reply_markup=await ClientKeyboard.menu_keyboard(user_info, lang)
    )


@router.callback_query(F.data == "get_lang")
async def get_language(query: Message, first: bool = False):
    q = query
    if isinstance(query, CallbackQuery):
        query = query.message
    try:
        await query.delete()
    except:
        pass

    if first:
        prefix = f"sel_lang|{query.from_user.id}"
    else:
        prefix = f"resel_lang|{q.from_user.id}"
    await query.answer("Select language",
                       reply_markup=await ClientKeyboard.languages_board(prefix))


@router.callback_query(F.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery):
    lang = await DataBase.get_lang(callback.from_user.id)
    try:
        member = await callback.bot.get_chat_member(CHANNEL_ID, callback.from_user.id)
        if member.status in ['member', 'administrator', 'creator']:
            await DataBase.set_subscription_status(callback.from_user.id, "yes")
            try:
                await callback.message.delete()
            except:
                pass
            await show_main_menu(callback.message, lang)
        else:
            await callback.answer(languages[lang]["not_subscribed"], show_alert=True)
    except:
        await callback.answer(languages[lang]["not_subscribed"], show_alert=True)

@router.callback_query(F.data.in_(["back", "check"]))
async def menu_output(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    lang = await DataBase.get_lang(callback.from_user.id)
    # Force refresh user info from database to get latest state
    user_info = await DataBase.get_user_info(callback.from_user.id)
    
    # Select photo based on language
    if lang == "ru":
        photo = types.FSInputFile("hello.jpg")
    elif lang == "ro":
        photo = types.FSInputFile("rohello.jpg")
    else:  # English
        photo = types.FSInputFile("hel.jpg")
    
    await callback.message.answer_photo(
        photo, 
        caption=languages[lang]["welcome_message"],
        parse_mode="HTML",
        reply_markup=await ClientKeyboard.menu_keyboard(user_info, lang)
    )
    await callback.answer()





@router.callback_query(F.data == "register")
async def register_handler(callback: types.CallbackQuery, state: FSMContext):
    lang = await DataBase.get_lang(callback.from_user.id)
    
    # Check if user is already registered
    user_info = await DataBase.get_user_info(callback.from_user.id)
    if user_info and user_info[0] == "reg":
        # User is already registered, redirect to deposit step
        try:
            await callback.message.delete()
        except:
            pass
        
        photo = types.FSInputFile("dep.png")
        dummy_callback = DummyCallback(callback.from_user.id)
        await callback.message.answer_photo(
            photo=photo,
            caption=languages[lang]["success_registration"],
            parse_mode="HTML",
            reply_markup=await ClientKeyboard.dep_keyboard(dummy_callback, lang)
        )
        return
    
    # User is not registered, show registration form
    text = languages[lang]["register_info"]
    try:
        await callback.message.delete()
    except:
        pass

    photo = types.FSInputFile("reger.png")
    await callback.message.answer_photo(
             photo=photo,
             caption=text,
             parse_mode="HTML",
             reply_markup=await ClientKeyboard.register_keyboard(callback, lang)
         )
    await state.set_state(RegisterState.input_id)


@router.callback_query(F.data == "need_deposit")
async def need_deposit_handler(callback: types.CallbackQuery):
    lang = await DataBase.get_lang(callback.from_user.id)
    
    # Check current user status
    user_info = await DataBase.get_user_info(callback.from_user.id)
    if not user_info or user_info[0] != "reg":
        # User is not registered, redirect to registration
        await register_handler(callback, None)
        return
    
    if user_info[3] == "dep":
        # User has already deposited, should not reach here but redirect to main menu
        await menu_output(callback)
        return
    
    # User is registered but needs to deposit
    try:
        await callback.message.delete()
    except:
        pass
    
    photo = types.FSInputFile("dep.png")
    dummy_callback = DummyCallback(callback.from_user.id)
    await callback.message.answer_photo(
        photo=photo,
        caption=languages[lang]["success_registration"],
        parse_mode="HTML",
        reply_markup=await ClientKeyboard.dep_keyboard(dummy_callback, lang)
    )

@router.message(RegisterState.input_id)
async def mailing_state(message: types.Message, state: FSMContext, bot: Bot):
    lang = await DataBase.get_lang(message.chat.id)
    if str(message.text).isnumeric()==True:
        text_capt = ''
        acc_id = message.text
        checked = await DataBase.check_register(message.chat.id)
        if checked == 0:
            await DataBase.register(message.chat.id,acc_id)
            text_capt = languages[lang]["success_registration"]
        else:
            text_capt = languages[lang]["check_register"]
        
        photo = types.FSInputFile("dep.png")
        dummy_callback = DummyCallback(message.chat.id)
        await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=photo,
            caption=text_capt,
            parse_mode="HTML",
            reply_markup=await ClientKeyboard.dep_keyboard(dummy_callback, lang)
        )
    else:
        lang = await DataBase.get_lang(message.chat.id)
        await show_main_menu(message, lang)

    
    await state.clear()


@router.callback_query(F.data == "instruction")
async def instruction_handler(callback: types.CallbackQuery):
    new_ref_url = await DataBase.get_ref()
    lang = await DataBase.get_lang(callback.from_user.id)
    text = languages[lang]["instruction_info"].format(ref_url=new_ref_url)

    try:
        await callback.message.delete()
    except:
        pass

    await callback.message.answer(text, reply_markup=await ClientKeyboard.back_keyboard(lang),
                                  parse_mode="HTML")






def deposit_required(func):
    async def wrapper(event, *args, **kwargs):
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            return
            
        deposit_status = await DataBase.get_deposit_status(user_id)
        if deposit_status != 'dep':
            lang = await DataBase.get_lang(user_id)
            await event.answer(
                languages[lang]["deposit_required"],
                show_alert=True
            )
            return
        
        return await func(event, *args, **kwargs)
    return wrapper


async def send_postback(postback_type: str, user_id: int, country: str = "", amount: str = ""):
    """Send postback notification to verification channel"""
    try:
        if postback_type == "register":
            message = f"{user_id}"
        elif postback_type == "firstdep":
            message = f"{user_id}|Firstdep|{amount}"
        else:  # regular deposit
            message = f"{user_id}|{country}|{amount}"
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        params = {
            'chat_id': VERIF_CHANNEL_ID,
            'text': message
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                return await response.json()
    except Exception as e:
        print(f"Error sending postback: {e}")


async def handle_postback_direct(message: types.Message):
    """Direct postback handler"""
    try:
        text = message.text.strip()
        parts = text.split('|')
        print(f"Processing postback: {text}, parts: {parts}")
        
        if len(parts) == 1:
            # Registration postback: just user_id
            user_id = int(parts[0])
            print(f"Registration postback for user: {user_id}")
            await DataBase.mark_user_registered(user_id)
            
            
            # Notify user and move to deposit step
            try:
                lang = await DataBase.get_lang(user_id)
                print(f"User {user_id} language: {lang}")
                if lang:
                    photo = types.FSInputFile("dep.png")
                    dummy_callback = DummyCallback(user_id)
                    await message.bot.send_photo(
                        chat_id=user_id,
                        photo=photo,
                        caption=languages[lang]["success_registration"],
                        parse_mode="HTML",
                        reply_markup=await ClientKeyboard.dep_keyboard(dummy_callback, lang)
                    )
                    print(f"Sent registration success message to user {user_id}")
            except Exception as e:
                print(f"Error sending registration message: {e}")
            
        elif len(parts) >= 2 and parts[1] == "Firstdep":
            # First deposit postback: user_id|Firstdep|amount
            user_id = int(parts[0])
            print(f"First deposit postback for user: {user_id}")
            await DataBase.mark_user_deposited(user_id)
            
            # Notify user and move to main menu
            try:
                lang = await DataBase.get_lang(user_id)
                print(f"User {user_id} language: {lang}")
                if lang:
                    await message.bot.send_message(
                        chat_id=user_id,
                        text=languages[lang]["deposit_verified"],
                        parse_mode="HTML",
                        reply_markup=await ClientKeyboard.deposit_verified_keyboard(lang)
                    )
                    print(f"Sent deposit verified message to user {user_id}")
            except Exception as e:
                print(f"Error sending deposit verification: {e}")
            
    except Exception as e:
        print(f"Error in postback handler: {e}")


@router.message(F.chat.id == int(VERIF_CHANNEL_ID))
async def handle_postback(message: types.Message):
    """Handle postback messages from verification channel"""
    print(f"Postback received: {message.text}")
    await handle_postback_direct(message)




