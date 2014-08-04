
begin;

create table merchant (
    id			smallint not null primary key,
    name		varchar(64) not null,
    code		varchar(32) not null
);

create table product (
    id			integer not null primary key,
    gtin		bigint not null unique,
    name		varchar(64) not null
);

create table merchant_product (
    merchant_id		smallint not null,
    product_id		integer not null,
    name		varchar(64) not null,
    price_usd           numeric(8,2) not null,
    foreign key (merchant_id) references merchant (id),
    foreign key (product_id)  references product  (id)
);

create index idx_mp_prod on merchant_product (product_id);

insert into merchant (id, name)
          select 1, 'Test Merchant 1', 'TM1'
union all select 2, 'Test Merchant 2', 'TM2'
union all select 3, 'Test Merchant 3', 'TM3'
;

insert into product (id, gtin, name)
          select 1, 012345678905, 'Test Product 1'
union all select 2, 012345678906, 'Test Product 2'
union all select 3, 012345678907, 'Test Product 3'
;

insert into merchant_product (merchant_id, product_id, name, price_usd)
          select 1, 1, 'Test Merchant Product 1', 100.00
union all select 2, 1, 'Test Merchant Product 2', 101.00
union all select 3, 1, 'Test Merchant Product 3', 102.00
;

commit;
