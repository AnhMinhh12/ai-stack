WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay, %s::time AS tu_gio, %s::time AS den_gio,
           coalesce(%s::text, '') AS line_code, coalesce(%s::text, '') AS id_oi,
           coalesce(%s::text, '') AS status, coalesce(%s::text, '') AS operation_code,
           coalesce(%s::text, '') AS branch_code, coalesce(%s::boolean, true) AS group_yn,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1 OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), oi_1 AS (
    SELECT c.id_oi AS oi_id1, max(c.machine_code) AS line_code, max(c.operation_code) AS operation_code,
           max(c.end_date) AS end_date, date_trunc('second', max(c.end_time)::time)::time AS end_time
    FROM public.mes_oi_confirm c CROSS JOIN scope s
    WHERE s.authorized_user_id IS NOT NULL
      AND c.end_date + c.end_time::time BETWEEN s.tu_ngay + s.tu_gio AND s.den_ngay + s.den_gio
      AND (s.line_code = '' OR c.machine_code = ANY(string_to_array(s.line_code, ',')))
      AND (s.operation_code = '' OR c.operation_code = ANY(string_to_array(s.operation_code, ',')))
      AND (s.id_oi = '' OR c.id_oi = ANY(string_to_array(s.id_oi, ',')))
      AND (s.branch_code = '' OR c.branch_code = ANY(string_to_array(s.branch_code, ',')))
      AND (s.unrestricted OR c.branch_code = ANY(string_to_array(s.ds_branchs, ',')))
    GROUP BY c.id_oi
), oi_pairs AS (
    SELECT o.*, n.id_oi AS oi_id2, n.create_date AS start_date, n.create_time::time AS start_time
    FROM oi_1 o
    CROSS JOIN scope s
    JOIN LATERAL (
        SELECT c.id_oi, x.date0 AS create_date, date_trunc('second', x.time0::time)::time AS create_time
        FROM public.mes_oi_confirm c JOIN public.new_oi_cbsx x ON x.id_oi = c.id_oi
        WHERE c.id_oi <> o.oi_id1 AND c.machine_code = o.line_code
          AND c.create_date + c.create_time::time >= o.end_date + o.end_time
        ORDER BY c.create_date, c.create_time
        LIMIT 1
    ) n ON true
), intervals AS (
    SELECT p.oi_id1, p.oi_id2, p.line_code, p.operation_code,
           CASE WHEN g.day_index = 0 THEN p.end_date ELSE g.day_value::date END AS end_date,
           CASE WHEN g.day_index = 0 THEN p.end_time ELSE time '08:00' END AS end_time,
           CASE WHEN g.day_index = g.max_index THEN p.start_date ELSE (g.day_value::date + 1) END AS start_date,
           CASE WHEN g.day_index = g.max_index THEN p.start_time ELSE time '08:00' END AS start_time
    FROM oi_pairs p
    CROSS JOIN LATERAL (
        SELECT d AS day_value, row_number() OVER (ORDER BY d) - 1 AS day_index,
               count(*) OVER () - 1 AS max_index
        FROM generate_series(p.end_date::date, p.start_date::date, interval '1 day') d
    ) g
), interval_values AS (
    SELECT i.*, round((extract(epoch FROM ((i.start_date::text || ' ' || i.start_time::text)::timestamp - (i.end_date::text || ' ' || i.end_time::text)::timestamp)) / 60)::numeric, 2) AS thoi_gian_dung
    FROM intervals i
), filtered AS (
    SELECT i.* FROM interval_values i CROSS JOIN scope s
    WHERE (s.status = '' OR s.status = '0'
           OR (s.status = '1' AND EXISTS (SELECT 1 FROM public.mes_oi_allocation_stop_line a GROUP BY a.oi_id1 HAVING a.oi_id1 = i.oi_id1 AND sum(a.thoi_gian_dung) = i.thoi_gian_dung))
           OR (s.status = '2' AND NOT EXISTS (SELECT 1 FROM public.mes_oi_allocation_stop_line a WHERE a.oi_id1 = i.oi_id1)))
), summary_rows AS (
    SELECT 5::smallint AS sysorder, row_number() OVER (ORDER BY i.line_code, i.operation_code, i.oi_id1, i.end_date, i.end_time) AS stt,
           i.line_code, i.operation_code, i.oi_id1, i.end_date, i.end_time, i.oi_id2, i.start_date, i.start_time,
           i.thoi_gian_dung, NULL::character varying AS ma_loi, NULL::character varying AS ten_loi,
           NULL::date AS start_date_loi, NULL::time AS start_time_loi, NULL::date AS end_date_loi, NULL::time AS end_time_loi,
           coalesce((SELECT sum(a.thoi_gian_dung) FROM public.mes_oi_allocation_stop_line a WHERE a.oi_id1 = i.oi_id1), 0) AS thoi_gian_dung_loi
    FROM filtered i
), detail_rows AS (
    SELECT 3::smallint AS sysorder, NULL::bigint AS stt, i.line_code, i.operation_code, i.oi_id1, i.end_date, i.end_time, i.oi_id2, i.start_date, i.start_time,
           NULL::numeric AS thoi_gian_dung, a.ma_loi, l.ten_loi, a.start_date AS start_date_loi, a.start_time::time AS start_time_loi,
           a.end_date AS end_date_loi, a.end_time::time AS end_time_loi, a.thoi_gian_dung AS thoi_gian_dung_loi
    FROM filtered i JOIN public.mes_oi_allocation_stop_line a ON a.oi_id1 = i.oi_id1
    LEFT JOIN public.dmnndungmay l ON l.ma_loi = a.ma_loi
), rows AS (
    SELECT * FROM summary_rows UNION ALL SELECT * FROM detail_rows
)
SELECT r.*, count(*) OVER () AS total
FROM rows r CROSS JOIN scope s
WHERE s.group_yn OR r.sysorder = 5
ORDER BY r.line_code, r.operation_code, r.oi_id1, r.end_date, r.end_time, r.sysorder DESC, r.stt
LIMIT (SELECT row_limit FROM params)
