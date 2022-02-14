create table if not exists groups (
    name             text        primary key,
    alias            text        unique,
    faculty_advisor  text,
    mobile           varchar(14) unique,
    branch           varchar(5)  unique,
    kind             text        check(kind in ('cultural club', 'technical club', 'technical society')),
    description      text
);

create table if not exists group_discord (
    name            text        references groups(name),
    id              bigint      unique,
    invite          varchar(10) unique,
    fresher_role    bigint      unique,
    sophomore_role  bigint      unique,
    junior_role     bigint      unique,
    senior_role     bigint      unique,
    guest_role      bigint      unique
);

create table if not exists group_socials (
    name  text references groups(name),
    type  varchar(15),
    link  text
);

create table if not exists group_admins (
    group_name   text references groups(name),
    position     varchar(20),
    roll_number  int  references students(roll_number)
);

create table if not exists group_members (
    roll_number  int  not null references students(roll_number),
    group_name   text not null references groups(name),
    primary key (roll_number, group_name)
);

create view if not exists group_discord_users as
    select students.batch, students.discord_uid,
        c.name, c.alias, d.id, d.invite,
        d.fresher_role, d.sophomore_role, d.junior_role, d.senior_role,
        d.guest_role
        from group_members m
        join groups c on c.name = m.group_name
        join group_discord d on d.name = m.group_name
        join students on students.roll_number = m.roll_number
        where students.discord_uid not null;
