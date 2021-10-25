create table if not exists guilds (
    ID              int  primary key,
    Name            text check(length(Name) <= 100) not null,
    Batch           int  check(Batch >= 2010),
    Bot_Role        int,
    Mute_Role       int,
    Edit_Channel    int,
    Delete_Channel  int
);

create table if not exists prefixes (
    ID      int  references guilds(ID),
    prefix  text not null,
    primary key (ID, prefix)
);

create table if not exists join_roles (
    ID    int references guilds(ID),
    role  int not null,
    primary key (ID, role)
);

create table if not exists mod_roles (
    ID    int references guilds(ID),
    role  int not null,
    primary key (ID, role)
);

create table if not exists verified_servers (
    Batch                int primary key references guilds(Batch),
    Instruction_Channel  int,
    Command_Channel      int,
    Guest_Role           int
);

create table if not exists events (
    Guild_ID         int references guilds(ID),
    Join_Channel     int,
    Join_Message     text default '{$user} has joined the server!',
    Leave_Channel    int,
    Leave_Message    text default '{$user} has left the server.',
    Kick_Channel     int,
    Kick_Message     text default '{$user} has been kicked from the server by {$member}.',
    Ban_Channel      int,
    Ban_Message      text default '{$user} has been banned from the server by {$member}.',
    Welcome_Message  text
);
