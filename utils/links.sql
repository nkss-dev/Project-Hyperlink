create table if not exists link_managers (
    Batch         int,
    Guild_ID      int,
    Manager_Role  int,
    primary key (Guild_ID, Manager_Role)
);

create table if not exists dashboards (
    Batch    int,
    Section  text,
    Channel  int primary key,
    Message  int unique
);

create table if not exists links (
    Batch    int,
    Section  text,
    Day      text,
    Subject  text,
    Time     text,
    Link     text,
    SubSecs  text,
    primary key (Batch, Section, Day, Subject, Time)
);