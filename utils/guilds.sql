CREATE TABLE IF NOT EXISTS guild (
    id              bigint primary key,
    name            text   check(length(name) <= 100) not null,
    batch           int    unique check(batch >= 0),
    language        text   default 'en-GB',
    bot_role        bigint,
    mute_role       bigint,
    edit_channel    bigint,
    delete_channel  bigint
);

CREATE TABLE IF NOT EXISTS prefix (
    id      bigint references guild(id),
    prefix  text   not null,
    primary key(id, prefix)
);

CREATE TABLE IF NOT EXISTS join_role (
    id    bigint references guild(id),
    role  bigint primary key
);

CREATE TABLE IF NOT EXISTS mod_role (
    id    bigint references guild(id),
    role  bigint primary key
);

CREATE TABLE IF NOT EXISTS verified_server (
    id                   bigint primary key references guild(id),
    batch                int    references guild(batch),
    instruction_channel  bigint,
    command_channel      bigint,
    guest_role           bigint
);

CREATE TABLE IF NOT EXISTS event (
    guild_id         bigint references guild(id),
    join_channel     bigint,
    join_message     text   default '{$user} has joined the server!',
    leave_channel    bigint,
    leave_message    text   default '{$user} has left the server.',
    kick_channel     bigint,
    kick_message     text   default '{$user} has been kicked from the server by {$member}.',
    ban_channel      bigint,
    ban_message      text   default '{$user} has been banned from the server by {$member}.',
    welcome_message  text
);
