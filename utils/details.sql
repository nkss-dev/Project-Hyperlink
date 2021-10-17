create table if not exists main (
    Roll_Number integer primary key,
    Section text,
    SubSection text,
    Name text,
    Gender text,
    Mobile text,
    Institute_Email text,
    Batch integer,
    Hostel_Number int,
    Room_Number text,
    Discord_UID integer unique,
    Verified text default 'False'
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
    Discord_UID integer,
    level text,
    coins text,
    total text,
    lose text,
    win text,
    rip text,
    message text,
    row text,
    col text,
    board text,
    flip text,
    bg blob,
    voltorb_tile blob,
    tile_1 blob,
    tile_2 blob,
    tile_3 blob,
    hl_voltorb_tile blob,
    foreign key(Discord_UID) references main(Discord_UID)
);
