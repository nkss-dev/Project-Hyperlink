create table if not exists hostels (
    Hostel_Number  text primary key check(Hostel_Number like '%H_%'),
    Hostel_Name    text unique,
    Warden_Name    text unique
);

create table if not exists main (
    Roll_Number      int  primary key,
    Section          text check(Section like '__-_'),
    SubSection       text check(SubSection like '__-0_'),
    Name             text not null,
    Gender           text check(Gender='Male' or Gender='Female' or Gender='Other'),
    Mobile           text unique,
    Birthday         date,
    Institute_Email  text check(Institute_Email like '%___@___%.__%'),
    Batch            int  check(Batch >= 0),
    Hostel_Number    text references hostels(Hostel_Number),
    Room_Number      text check(Room_Number like '%_-___'),
    Discord_UID      int  unique,
    Verified         boolean
);

create table if not exists groups (
    Name             text primary key,
    Alias            text unique,
    Faculty_Advisor  text,
    Contact_Number   text,
    Branch           text unique,
    Kind             text check(Kind='Cultural Club' or Kind='Technical Club' or Kind='Technical Society'),
    Discord_Server   int  unique,
    Server_Invite    text unique,
    Fresher_Role     int  unique,
    Sophomore_Role   int  unique,
    Junior_Role      int  unique,
    Senior_Role      int  unique,
    Guest_Role       int  unique
);

create table if not exists group_members (
    Roll_Number  int  not null references main(Roll_Number),
    Group_Name   text not null references groups(Name),
    primary key (Roll_Number, Group_Name)
);

create view if not exists group_discord_users as
    select main.Batch, main.Discord_UID,
        c.Name, c.Alias, c.Discord_Server, c.Server_Invite,
        c.Fresher_Role, c.Sophomore_Role, c.Junior_Role, c.Senior_Role,
        c.Guest_Role
        from group_members m
        join groups c on c.Name = m.Group_Name
        join main on main.Roll_Number = m.Roll_Number
        where main.Discord_UID not null;

create table if not exists ign (
    `Discord_UID`     int primary key,
    `Chess`           text,
    `Clash of Clans`  text,
    `Clash Royale`    text,
    `Call of Duty`    text,
    `CSGO`            text,
    `Fortnite`        text,
    `Genshin Impact`  text,
    `GTAV`            text,
    `Minecraft`       text,
    `osu!`            text,
    `Paladins`        text,
    `PUBG`            text,
    `Rocket League`   text,
    `Valorant`        text,
    foreign key(Discord_UID) references main(Discord_UID) on update cascade
);

create table if not exists voltorb (
    Discord_UID      int,
    level            text,
    coins            text,
    total            text,
    lose             text,
    win              text,
    rip              text,
    message          text,
    row              text,
    col              text,
    board            text,
    flip             text,
    bg               text,
    voltorb_tile     text,
    tile_1           text,
    tile_2           text,
    tile_3           text,
    hl_voltorb_tile  text,
    foreign key(Discord_UID) references main(Discord_UID)
);
