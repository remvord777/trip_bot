from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.email_targets import email_targets_keyboard
from data.email_targets import EMAIL_TARGETS
from states.email import EmailStates
from utils.mailer import send_email

router = Router()


@router.callback_query(EmailStates.select_recipients)
async def email_select(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = set(data.get("email_targets", []))

    action = call.data.split(":")[1]

    if action == "send":
        recipients = []
        for key in selected:
            recipients.extend(EMAIL_TARGETS[key]["emails"])

        # сохраняем в FSM
        await state.update_data(email_recipients=recipients)

        # 👉 тут вызывается send_email(...) с recipients
        # (я ниже покажу)

        await call.message.answer(
            "📧 Документы отправлены:\n" +
            "\n".join(f"• {email}" for email in recipients)
        )
        await state.clear()
        await call.answer()
        return

    # toggle
    if action in selected:
        selected.remove(action)
    else:
        selected.add(action)

    await state.update_data(email_targets=list(selected))
    await call.message.edit_reply_markup(
        reply_markup=email_targets_keyboard(selected)
    )
    await call.answer()
