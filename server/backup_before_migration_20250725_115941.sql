--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13
-- Dumped by pg_dump version 15.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO "user";

--
-- Name: household_members; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.household_members (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid NOT NULL,
    household_id uuid NOT NULL,
    role character varying(50) NOT NULL,
    joined_at timestamp without time zone NOT NULL
);


ALTER TABLE public.household_members OWNER TO "user";

--
-- Name: households; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.households (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying(255) NOT NULL,
    invite_code character varying(6) NOT NULL,
    owner_id uuid NOT NULL,
    settings jsonb
);


ALTER TABLE public.households OWNER TO "user";

--
-- Name: order_items; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.order_items (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying(255) NOT NULL,
    quantity double precision NOT NULL,
    unit character varying(50),
    unit_price double precision,
    total_price double precision,
    barcode character varying(50),
    brand character varying(100),
    size character varying(50),
    order_id uuid NOT NULL,
    shopping_list_item_id uuid,
    external_item_data jsonb
);


ALTER TABLE public.order_items OWNER TO "user";

--
-- Name: orders; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.orders (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    external_order_id character varying(100),
    service_provider character varying(50),
    total_amount double precision,
    tax_amount double precision,
    delivery_fee double precision,
    tip_amount double precision,
    status character varying(50),
    estimated_delivery timestamp without time zone,
    actual_delivery timestamp without time zone,
    delivery_address jsonb,
    delivery_instructions text,
    user_id uuid NOT NULL,
    household_id uuid NOT NULL,
    shopping_list_id uuid,
    affiliate_tracking_id character varying(100),
    order_metadata jsonb
);


ALTER TABLE public.orders OWNER TO "user";

--
-- Name: pantry_categories; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.pantry_categories (
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    icon character varying(50),
    color character varying(7)
);


ALTER TABLE public.pantry_categories OWNER TO "user";

--
-- Name: pantry_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.pantry_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.pantry_categories_id_seq OWNER TO "user";

--
-- Name: pantry_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.pantry_categories_id_seq OWNED BY public.pantry_categories.id;


--
-- Name: pantry_items; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.pantry_items (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying(255) NOT NULL,
    barcode character varying(50),
    quantity double precision NOT NULL,
    unit character varying(50),
    expiration_date date,
    purchase_date date,
    location character varying(100),
    notes text,
    household_id uuid NOT NULL,
    category_id integer,
    added_by_user_id uuid NOT NULL,
    item_metadata jsonb
);


ALTER TABLE public.pantry_items OWNER TO "user";

--
-- Name: recipe_ingredients; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.recipe_ingredients (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    recipe_id integer NOT NULL,
    name character varying(255) NOT NULL,
    quantity double precision,
    unit character varying(50),
    notes character varying(255),
    is_optional character varying(10)
);


ALTER TABLE public.recipe_ingredients OWNER TO "user";

--
-- Name: recipes; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.recipes (
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    title character varying(255) NOT NULL,
    description text,
    instructions text NOT NULL,
    prep_time_minutes integer,
    cook_time_minutes integer,
    servings integer,
    difficulty_level character varying(20),
    nutrition_info jsonb,
    tags jsonb,
    cuisine_type character varying(100),
    external_source character varying(255),
    external_id character varying(100)
);


ALTER TABLE public.recipes OWNER TO "user";

--
-- Name: recipes_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.recipes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.recipes_id_seq OWNER TO "user";

--
-- Name: recipes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.recipes_id_seq OWNED BY public.recipes.id;


--
-- Name: shopping_list_items; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.shopping_list_items (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying(255) NOT NULL,
    quantity double precision,
    unit character varying(50),
    notes text,
    is_purchased boolean,
    priority character varying(20),
    estimated_price double precision,
    actual_price double precision,
    shopping_list_id uuid NOT NULL,
    added_by_user_id uuid NOT NULL,
    recipe_id integer
);


ALTER TABLE public.shopping_list_items OWNER TO "user";

--
-- Name: shopping_lists; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.shopping_lists (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    status character varying(50),
    is_shared boolean,
    household_id uuid NOT NULL,
    created_by_user_id uuid NOT NULL,
    list_metadata jsonb
);


ALTER TABLE public.shopping_lists OWNER TO "user";

--
-- Name: user_favorites; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.user_favorites (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid NOT NULL,
    recipe_id integer NOT NULL,
    rating integer,
    notes text
);


ALTER TABLE public.user_favorites OWNER TO "user";

--
-- Name: users; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.users (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    email character varying(255) NOT NULL,
    full_name character varying(255) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    is_verified boolean DEFAULT false NOT NULL,
    dietary_preferences jsonb,
    voice_settings jsonb,
    notification_preferences jsonb
);


ALTER TABLE public.users OWNER TO "user";

--
-- Name: pantry_categories id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pantry_categories ALTER COLUMN id SET DEFAULT nextval('public.pantry_categories_id_seq'::regclass);


--
-- Name: recipes id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.recipes ALTER COLUMN id SET DEFAULT nextval('public.recipes_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.alembic_version (version_num) FROM stdin;
c3f6ba074872
\.


--
-- Data for Name: household_members; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.household_members (id, created_at, updated_at, user_id, household_id, role, joined_at) FROM stdin;
\.


--
-- Data for Name: households; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.households (id, created_at, updated_at, name, invite_code, owner_id, settings) FROM stdin;
\.


--
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.order_items (id, created_at, updated_at, name, quantity, unit, unit_price, total_price, barcode, brand, size, order_id, shopping_list_item_id, external_item_data) FROM stdin;
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.orders (id, created_at, updated_at, external_order_id, service_provider, total_amount, tax_amount, delivery_fee, tip_amount, status, estimated_delivery, actual_delivery, delivery_address, delivery_instructions, user_id, household_id, shopping_list_id, affiliate_tracking_id, order_metadata) FROM stdin;
\.


--
-- Data for Name: pantry_categories; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.pantry_categories (id, created_at, updated_at, name, description, icon, color) FROM stdin;
\.


--
-- Data for Name: pantry_items; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.pantry_items (id, created_at, updated_at, name, barcode, quantity, unit, expiration_date, purchase_date, location, notes, household_id, category_id, added_by_user_id, item_metadata) FROM stdin;
\.


--
-- Data for Name: recipe_ingredients; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.recipe_ingredients (id, created_at, updated_at, recipe_id, name, quantity, unit, notes, is_optional) FROM stdin;
\.


--
-- Data for Name: recipes; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.recipes (id, created_at, updated_at, title, description, instructions, prep_time_minutes, cook_time_minutes, servings, difficulty_level, nutrition_info, tags, cuisine_type, external_source, external_id) FROM stdin;
\.


--
-- Data for Name: shopping_list_items; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.shopping_list_items (id, created_at, updated_at, name, quantity, unit, notes, is_purchased, priority, estimated_price, actual_price, shopping_list_id, added_by_user_id, recipe_id) FROM stdin;
\.


--
-- Data for Name: shopping_lists; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.shopping_lists (id, created_at, updated_at, name, description, status, is_shared, household_id, created_by_user_id, list_metadata) FROM stdin;
\.


--
-- Data for Name: user_favorites; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.user_favorites (id, created_at, updated_at, user_id, recipe_id, rating, notes) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.users (id, created_at, updated_at, email, full_name, is_active, is_verified, dietary_preferences, voice_settings, notification_preferences) FROM stdin;
\.


--
-- Name: pantry_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.pantry_categories_id_seq', 1, false);


--
-- Name: recipes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.recipes_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: household_members household_members_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.household_members
    ADD CONSTRAINT household_members_pkey PRIMARY KEY (id);


--
-- Name: households households_invite_code_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.households
    ADD CONSTRAINT households_invite_code_key UNIQUE (invite_code);


--
-- Name: households households_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.households
    ADD CONSTRAINT households_pkey PRIMARY KEY (id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);


--
-- Name: orders orders_external_order_id_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_external_order_id_key UNIQUE (external_order_id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: pantry_categories pantry_categories_name_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pantry_categories
    ADD CONSTRAINT pantry_categories_name_key UNIQUE (name);


--
-- Name: pantry_categories pantry_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pantry_categories
    ADD CONSTRAINT pantry_categories_pkey PRIMARY KEY (id);


--
-- Name: pantry_items pantry_items_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pantry_items
    ADD CONSTRAINT pantry_items_pkey PRIMARY KEY (id);


--
-- Name: recipe_ingredients recipe_ingredients_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.recipe_ingredients
    ADD CONSTRAINT recipe_ingredients_pkey PRIMARY KEY (id);


--
-- Name: recipes recipes_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT recipes_pkey PRIMARY KEY (id);


--
-- Name: shopping_list_items shopping_list_items_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.shopping_list_items
    ADD CONSTRAINT shopping_list_items_pkey PRIMARY KEY (id);


--
-- Name: shopping_lists shopping_lists_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.shopping_lists
    ADD CONSTRAINT shopping_lists_pkey PRIMARY KEY (id);


--
-- Name: household_members unique_user_household; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.household_members
    ADD CONSTRAINT unique_user_household UNIQUE (user_id, household_id);


--
-- Name: user_favorites unique_user_recipe_favorite; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.user_favorites
    ADD CONSTRAINT unique_user_recipe_favorite UNIQUE (user_id, recipe_id);


--
-- Name: user_favorites user_favorites_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.user_favorites
    ADD CONSTRAINT user_favorites_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_household_members_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_household_members_id ON public.household_members USING btree (id);


--
-- Name: ix_households_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_households_id ON public.households USING btree (id);


--
-- Name: ix_households_invite_code; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_households_invite_code ON public.households USING btree (invite_code);


--
-- Name: ix_order_items_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_order_items_id ON public.order_items USING btree (id);


--
-- Name: ix_orders_external_order_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_orders_external_order_id ON public.orders USING btree (external_order_id);


--
-- Name: ix_orders_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_orders_id ON public.orders USING btree (id);


--
-- Name: ix_pantry_categories_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_pantry_categories_id ON public.pantry_categories USING btree (id);


--
-- Name: ix_pantry_items_barcode; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_pantry_items_barcode ON public.pantry_items USING btree (barcode);


--
-- Name: ix_pantry_items_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_pantry_items_id ON public.pantry_items USING btree (id);


--
-- Name: ix_recipe_ingredients_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_recipe_ingredients_id ON public.recipe_ingredients USING btree (id);


--
-- Name: ix_recipes_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_recipes_id ON public.recipes USING btree (id);


--
-- Name: ix_shopping_list_items_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_shopping_list_items_id ON public.shopping_list_items USING btree (id);


--
-- Name: ix_shopping_lists_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_shopping_lists_id ON public.shopping_lists USING btree (id);


--
-- Name: ix_user_favorites_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_user_favorites_id ON public.user_favorites USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: household_members household_members_household_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.household_members
    ADD CONSTRAINT household_members_household_id_fkey FOREIGN KEY (household_id) REFERENCES public.households(id);


--
-- Name: household_members household_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.household_members
    ADD CONSTRAINT household_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: households households_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.households
    ADD CONSTRAINT households_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: order_items order_items_shopping_list_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_shopping_list_item_id_fkey FOREIGN KEY (shopping_list_item_id) REFERENCES public.shopping_list_items(id);


--
-- Name: orders orders_household_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_household_id_fkey FOREIGN KEY (household_id) REFERENCES public.households(id);


--
-- Name: orders orders_shopping_list_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_shopping_list_id_fkey FOREIGN KEY (shopping_list_id) REFERENCES public.shopping_lists(id);


--
-- Name: orders orders_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: pantry_items pantry_items_added_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pantry_items
    ADD CONSTRAINT pantry_items_added_by_user_id_fkey FOREIGN KEY (added_by_user_id) REFERENCES public.users(id);


--
-- Name: pantry_items pantry_items_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pantry_items
    ADD CONSTRAINT pantry_items_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.pantry_categories(id);


--
-- Name: pantry_items pantry_items_household_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pantry_items
    ADD CONSTRAINT pantry_items_household_id_fkey FOREIGN KEY (household_id) REFERENCES public.households(id);


--
-- Name: recipe_ingredients recipe_ingredients_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.recipe_ingredients
    ADD CONSTRAINT recipe_ingredients_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id);


--
-- Name: shopping_list_items shopping_list_items_added_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.shopping_list_items
    ADD CONSTRAINT shopping_list_items_added_by_user_id_fkey FOREIGN KEY (added_by_user_id) REFERENCES public.users(id);


--
-- Name: shopping_list_items shopping_list_items_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.shopping_list_items
    ADD CONSTRAINT shopping_list_items_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id);


--
-- Name: shopping_list_items shopping_list_items_shopping_list_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.shopping_list_items
    ADD CONSTRAINT shopping_list_items_shopping_list_id_fkey FOREIGN KEY (shopping_list_id) REFERENCES public.shopping_lists(id);


--
-- Name: shopping_lists shopping_lists_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.shopping_lists
    ADD CONSTRAINT shopping_lists_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(id);


--
-- Name: shopping_lists shopping_lists_household_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.shopping_lists
    ADD CONSTRAINT shopping_lists_household_id_fkey FOREIGN KEY (household_id) REFERENCES public.households(id);


--
-- Name: user_favorites user_favorites_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.user_favorites
    ADD CONSTRAINT user_favorites_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id);


--
-- Name: user_favorites user_favorites_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.user_favorites
    ADD CONSTRAINT user_favorites_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

