create table if not exists hostels (
    number       varchar(4) primary key check(number like '%H_%'),
    name         text       unique,
    warden_name  text       unique
);

create table if not exists students (
    roll_number    int         primary key,
    section        char(4)     check(section like '__-_'),
    sub_section    char(5)     check(sub_section like '__-__'),
    name           varchar     not null,
    gender         char(1)     check(gender='M' or gender='F' or gender='O'),
    mobile         varchar(14) unique,
    birthday       date,
    email          text        check(email like '%___@nitkkr.ac.in'),
    batch          smallint    check(batch >= 0),
    hostel_number  varchar(4)  references hostels(hostel_number),
    room_number    varchar(6)  check(room_number like '%_-___'),
    discord_uid    bigint      unique,
    verified       boolean
);

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
