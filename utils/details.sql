create table if not exists hostel (
    Hostel_Number  text primary key check(Hostel_Number like '%H_'),
    Hostel_Name    text unique,
    Warden_Name    text unique
);

create table if not exists main (
    Roll_Number      int  primary key,
    Section          text check(Section like '__-_'),
    SubSection       text check(SubSection like '__-0_'),
    Name             text,
    Gender           text check(Gender='Male' or Gender='Female' or Gender='Other'),
    Mobile           text unique,
    Birthday         date,
    Institute_Email  text check(Institute_Email like '%___@___%.__%'),
    Batch            int  check(length(Batch)=4),
    Hostel_Number    text,
    Room_Number      text check(Room_Number like '%_-___') unique,
    Discord_UID      int  unique,
    Verified         text check(Verified='True' or Verified='False') default 'False',
    foreign key(Hostel_Number) references hostel(Hostel_Number)
);

create table if not exists ign (
    `Discord_UID`     int primary key not null,
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
    foreign key(Discord_UID) references main(Discord_UID)
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
