create table if not exists hostels (
    Hostel_Number  text primary key check(Hostel_Number like '%H_'),
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
    Batch            int  check(Batch >= 2010),
    Hostel_Number    text references hostels(Hostel_Number),
    Room_Number      text check(Room_Number like '%_-___') unique,
    Discord_UID      int  unique,
    Verified         boolean default false
);

create table if not exists groups (
    Name             text primary key,
    Faculty_Advisor  text,
    Contact_Number   text,
    Kind             text check(Kind='Cultural Club' or Kind='Technical Society'),
    Discord_Server   int,
    Fresher_Role     int,
    Sophomore_Role   int,
    Junior_Role      int,
    Final_Role       int,
    Guest_Role       int
);

create table if not exists group_members (
    Roll_Number  int  references main(Roll_Number),
    Group_Name   text references groups(Name),
    primary key(Roll_Number, Group_Name)
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
