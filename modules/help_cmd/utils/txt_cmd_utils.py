from typing import Any, Literal, Union

from discord import Attachment, Locale
from discord.app_commands import Command as AppCommand
from discord.app_commands.translator import (TranslationContext,
                                             TranslationContextLocation,
                                             locale_str)
from discord.ext import commands

from core.bot_classes import MyContext

from .utils import extract_info, get_discord_locale


async def get_command_inline_desc(ctx: MyContext, cmd: commands.Command):
    "Generate a 1-line description with the command name and short desc"
    name = await get_command_name_translation(ctx, cmd)
    short = await get_command_desc_translation(ctx, cmd) or cmd.short_doc.strip()
    return f"• **{name}**" + (f"  *{short}*" if short else "")


async def get_command_description(ctx: MyContext, command: commands.Command):
    "Get the parsed description of a command"
    raw_desc = command.description.strip()
    if raw_desc == '' and command.help is not None:
        raw_desc = command.help.strip()
    desc = str | None
    desc, examples, doc = await extract_info(raw_desc)
    # check for translated description
    if short_desc := await get_command_desc_translation(ctx, command):
        if len(desc.split("\n")) > 1:
            long_desc = "\n".join(desc.split("\n")[1:]).strip()
            desc = f"{short_desc}\n\n{long_desc}"
        else:
            desc = short_desc
    if desc is None:
        desc = await ctx.bot._(ctx.channel, "help.no-desc-cmd")
    return desc, examples, doc

async def get_command_signature(ctx: MyContext, command: commands.Command):
    "Get the signature of a command"
    # prefix
    if isinstance(command, AppCommand | commands.HybridCommand | commands.HybridGroup):
        prefix = '/'
    else:
        prefix = '@' + ctx.bot.user.name + ' '
    # name
    translated_name = await get_command_full_name_translation(ctx, command)
    # parameters
    signature = await _get_command_params_signature(ctx, command)
    return f"{prefix}{translated_name} {signature}".strip()

async def get_command_full_name_translation(ctx: MyContext, command: commands.Command):
    "Get the translated command or group name (with parent name if exists)"
    locale = await get_discord_locale(ctx)
    full_name = await get_command_name_translation(ctx, command, locale)
    while command.parent is not None:
        full_name = await get_command_name_translation(ctx, command.parent, locale) + " " + full_name
        command = command.parent
    return full_name

async def get_command_name_translation(ctx: MyContext, command: commands.Command, locale: Locale | None=None):
    "Get the translated command or group name (without parent name)"
    locale = locale or await get_discord_locale(ctx)
    if isinstance(command, commands.Group):
        context = TranslationContext(
            TranslationContextLocation.group_name,
            command
        )
    else:
        context = TranslationContext(
            TranslationContextLocation.command_name,
            command
        )
    return await ctx.bot.tree.translator.translate(locale_str(""), locale, context) or command.name

async def get_command_desc_translation(ctx: MyContext, command: commands.Command):
    "Get the translated command or group description"
    locale = await get_discord_locale(ctx)
    if isinstance(command, commands.Group):
        context = TranslationContext(
            TranslationContextLocation.group_description,
            command
        )
    else:
        context = TranslationContext(
            TranslationContextLocation.command_description,
            command
        )
    return await ctx.bot.tree.translator.translate(locale_str(""), locale, context)

async def _get_command_param_translation(ctx: MyContext, param: commands.Parameter, command: commands.HybridCommand):
    "Get the translated command parameter name"
    locale = await get_discord_locale(ctx)
    class FakeParameter:
        def __init__(self, command: AppCommand | commands.HybridCommand):
            self.command = command
    context = TranslationContext(
        TranslationContextLocation.parameter_name,
        FakeParameter(command)
    )
    return await ctx.bot.tree.translator.translate(locale_str(param.name), locale, context) or param.name

async def _get_command_params_signature(ctx: MyContext, command: commands.Command):
    "Returns a POSIX-like signature useful for help command output."
    if command.usage is not None:
        return command.usage

    params = command.clean_params
    if not params:
        return ''
    result = []
    for param in params.values():
        name = await _get_command_param_translation(ctx, param, command)
        greedy = isinstance(param.converter, commands.Greedy)
        optional = False  # postpone evaluation of if it's an optional argument

        annotation: Any = param.converter.converter if greedy else param.converter
        origin = getattr(annotation, "__origin__", None)
        if not greedy and origin is Union:
            none_cls = type(None)
            union_args = annotation.__args__
            optional = union_args[-1] is none_cls
            if len(union_args) == 2 and optional:
                annotation = union_args[0]
                origin = getattr(annotation, "__origin__", None)

        if annotation is Attachment:
            # For discord.Attachment we need to signal to the user that it's an attachment
            # It's not exactly pretty but it's enough to differentiate
            if optional:
                result.append(f"[{name} (upload a file)]")
            elif greedy:
                result.append(f"[{name} (upload files)]...")
            else:
                result.append(f"<{name} (upload a file)>")
            continue

        # for typing.Literal[...], typing.Optional[typing.Literal[...]], and Greedy[typing.Literal[...]], the
        # parameter signature is a literal list of it's values
        if origin is Literal:
            name = '|'.join(f'"{v}"' if isinstance(v, str) else str(v) for v in annotation.__args__)
        if not param.required:
            # We don't want None or '' to trigger the [name=value] case and instead it should
            # do [name] since [name=None] or [name=] are not exactly useful for the user.
            if param.displayed_default:
                result.append(
                    f"[{name}={param.displayed_default}]" if not greedy else f"[{name}={param.displayed_default}]..."
                )
                continue
            else:
                result.append(f"[{name}]")

        elif param.kind == param.VAR_POSITIONAL:
            if command.require_var_positional:
                result.append(f"<{name}...>")
            else:
                result.append(f"[{name}...]")
        elif greedy:
            result.append(f"[{name}]...")
        elif optional:
            result.append(f"[{name}]")
        else:
            result.append(f"<{name}>")

    return ' '.join(result)
