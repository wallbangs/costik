from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from other.languages import languages
from config import SUPP


class ClientKeyboard:


    @staticmethod
    async def languages_board(data: str):
        ikb = InlineKeyboardBuilder()
        ikb.button(text="🇷🇺 Русский", callback_data=f"{data}|ru")
        ikb.button(text="🇬🇧 English", callback_data=f"{data}|en")
        ikb.button(text="🇷🇴 Română", callback_data=f"{data}|ro")
        ikb.adjust(3)
        return ikb.as_markup()

    @staticmethod
    async def subscription_keyboard(lang: str, channel_url: str):
        ikb = InlineKeyboardBuilder()
        ikb.button(text=languages[lang]["subscribe_channel"], url=channel_url)
        ikb.button(text=languages[lang]["check_subscription"], callback_data="check_sub")
        ikb.adjust(1)
        return ikb.as_markup()

    @staticmethod
    async def menu_keyboard(user_info: list, lang: str):
        print(user_info)
        ikb = InlineKeyboardBuilder()
        
        # Only show registration button if user is not registered
        # user_info format: [verifed, user_id, lang, deposit]
        # Check index 0 (verifed field) for "reg" status
        if user_info is None or len(user_info) < 1 or user_info[0] != "reg":
            ikb.button(text=languages[lang]["register"], callback_data="register")
        
        ikb.button(text=languages[lang]["instruction"], callback_data="instruction")
        ikb.button(text=languages[lang]["support"], url=SUPP)
        ikb.button(text=languages[lang]["choose_lang"], callback_data="get_lang")

        # Check if user has deposited - show webapp if deposited
        if user_info is not None and len(user_info) >= 4 and user_info[3] == "dep":
            ikb.button(text=languages[lang]["get_signal"], web_app=types.WebAppInfo(url="https://wallbangs.github.io/topskitmomentos/"))
        elif user_info is not None and len(user_info) >= 1 and user_info[0] == "reg":
            # User is registered but not deposited - redirect to deposit
            ikb.button(text=languages[lang]["get_signal"], callback_data="need_deposit")
        else:
            # User is not registered - redirect to registration
            ikb.button(text=languages[lang]["get_signal"], callback_data="register")

        # Adjust layout based on whether registration button is shown
        if user_info is None or len(user_info) < 1 or user_info[0] != "reg":
            ikb.adjust(2, 2, 1)  # reg, instruction+support, lang, signal
        else:
            ikb.adjust(2, 1, 1)  # instruction+support, lang, signal
        return ikb.as_markup()

    @staticmethod
    async def register_keyboard(callback: types.CallbackQuery, lang: str):
        ikb = InlineKeyboardBuilder()
        # Create registration URL with user ID as sub1 parameter
        base_url = "https://1wdzjb.life/?p=9o7w"
        user_id = callback.from_user.id
        registration_url = f"{base_url}&sub1={user_id}"
        
        ikb.button(text=languages[lang]["register_action"], url=registration_url)
        ikb.button(text=languages[lang]["back"], callback_data="back")
        ikb.adjust(1)
        return ikb.as_markup()

    @staticmethod
    async def dep_keyboard(callback: types.CallbackQuery, lang: str):
        ikb = InlineKeyboardBuilder()
        # Create deposit URL with user ID as sub1 parameter
        base_url = "https://1wdzjb.life/?p=9o7w"
        user_id = callback.from_user.id
        deposit_url = f"{base_url}&sub1={user_id}"
        
        ikb.button(text=languages[lang]["dep_action"], url=deposit_url)
        ikb.button(text=languages[lang]["back"], callback_data="back")
        ikb.adjust(1)
        return ikb.as_markup()

    @staticmethod
    async def back_keyboard(lang: str):
        ikb = InlineKeyboardBuilder()
        ikb.button(text=languages[lang]["back"], callback_data="back")
        return ikb.as_markup()

    @staticmethod
    async def deposit_verified_keyboard(lang: str):
        ikb = InlineKeyboardBuilder()
        ikb.button(text=languages[lang]["get_signal"], web_app=types.WebAppInfo(url="https://wallbangs.github.io/topskitmomentos/"))
        ikb.button(text=languages[lang]["back"], callback_data="back")
        ikb.adjust(1)
        return ikb.as_markup()


