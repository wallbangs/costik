from aiogram.utils.keyboard import InlineKeyboardBuilder

async def admin_command():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="Рассылка 📩", callback_data="mailing")
    ikb.button(text="Смена реферальной ссылки 🔗", callback_data="change_ref")
    ikb.button(text="Статистика 📊", callback_data="stat")
    ikb.button(text="Установить верификацию", callback_data="verificate")
    ikb.button(text="Сбросить пользователя 🔄", callback_data="demote_user")
    ikb.button(text="Удалить пользователя ❌", callback_data="reset_user")
    ikb.adjust(2, 2, 2)
    return ikb.as_markup()

