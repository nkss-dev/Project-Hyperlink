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
    Guilds text default '[]',
    Verified text default 'False',
    IGN text default '{}'
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
