CREATE OR REPLACE FUNCTION public.sobctiendogh(params character varying)
 RETURNS SETOF sobctiendogh_return
 LANGUAGE plpgsql
AS $function$
DECLARE
    -- BÁO CÁO TIẾN ĐỘ GIAO HÀNG
    r sobctiendogh_return;
    r1 record;
    strSQL character varying;
    dynamicjs json;
    result record;
    _user_id smallint;
    dfrom ud_ngay;
    dto ud_ngay;
    cso_ct1 character varying;
    cso_ct2 character varying;
    cma_kh character varying;
    cma_kho character varying;
    cma_vt character varying;
    cnh_vt1 character varying;
    cnh_vt2 character varying;
    cnh_vt3 character varying;
    cnh_vt4 character varying;
    cnh_vt5 character varying;
    cloai_vt character varying;
    ctk_vt character varying;
    ctk_dt character varying;
    cma_vv character varying;
    cma_nvbh character varying;
    cma_dvcs character varying;
    cgroup character varying;
    cstatus character varying;
	cculture character varying;
    _stt smallint = 0;

	sqlRes  character varying;
	_listWhereCol character varying := '';
        _listWhereColAs character varying := '';

	keyword character varying := '';
        _sql character varying := '';

        pgridid character varying := '';
	_total bigint;

	r_json json; 
	r_item record; rc record;
	array_temp character varying := '';
	
	_M_ROUND_GIA_NT smallint:=0;
	_M_ROUND_GIA smallint :=0; 

	--phân quyền kho, đvcs
	_where_kho character varying:=' and 1=1 ';
	_where_dvcs character varying:=' and 1=1 ';  
    
    /*
     select * from sobctiendogh('{"JSON":{"user_id":"1","searchDynamic":
{
    "dfrom": "2026-05-01",
    "dto": "2026-05-20",
    "cso_ct1": "",
    "cso_ct2": "",
    "cma_kh": "",
    "cma_kho": "",
    "cma_vt": "ERPTEST-1",
    "cnh_vt1": "",
    "cnh_vt2": "",
    "cnh_vt3": "",
    "cnh_vt4": "",
    "cnh_vt5": "",
    "cma_dvcs": "001",
    "cstatus": "",
    "cgroup": "1",
    "mau_bc": "001",
    "gridid": "SOBCTienDoGH",
    "culture": "vi-VN"
} }}')

     select * from sobctiendogh('{"JSON":{"user_id":"10","searchDynamic":
 {"dfrom":"2021-07-01","dto":"2021-08-01","cso_ct1":"","cso_ct2":"","cma_kh":"","cma_kho":"","cma_vt":"","cnh_vt1":"","cnh_vt2":"","cnh_vt3":"","cnh_vt4":"","cnh_vt5":"","cma_dvcs":"001","mau_bc":"001","gridid":"SOBCTienDoGH","culture":"vi-VN"}
    }}')

     select * from userinfo where user_name like 'SALES%'
   */
BEGIN
	result := convert_json(params);
	_user_id := result.user_id;
	dynamicjs := result.pjson;
	-- raise notice 'dynamic %', dynamicjs;
	dfrom :=json_get(dynamicjs,'dfrom');
        dto :=json_get(dynamicjs,'dto');
        cso_ct1 :=json_get(dynamicjs,'cso_ct1');
        cso_ct2 :=json_get(dynamicjs,'cso_ct2');
	cma_kh :=json_get(dynamicjs,'cma_kh');
	cma_kho :=json_get(dynamicjs,'cma_kho');
	cma_vt :=json_get(dynamicjs,'cma_vt');
	cnh_vt1 :=json_get(dynamicjs,'cnh_vt1');
	cnh_vt2 :=json_get(dynamicjs,'cnh_vt2');
	cnh_vt3 :=json_get(dynamicjs,'cnh_vt3');
	cnh_vt4 :=json_get(dynamicjs,'cnh_vt4');
	cnh_vt5 :=json_get(dynamicjs,'cnh_vt5');
	cloai_vt :=json_get(dynamicjs,'cloai_vt');
	ctk_vt :=json_get(dynamicjs,'ctk_vt');
	ctk_dt :=json_get(dynamicjs,'ctk_dt');
	cma_vv :=json_get(dynamicjs,'cma_vv');
	cma_nvbh :=json_get(dynamicjs,'cma_nvbh');
	cma_dvcs :=json_get(dynamicjs,'cma_dvcs');
	cgroup :=json_get(dynamicjs,'cgroup');
	cculture :=json_get(dynamicjs,'culture');
	cstatus :=json_get(dynamicjs,'cstatus');
	cgroup :=json_get(dynamicjs,'cgroup');
	

	select value1 from sys_options where trim(option_name) = 'M_ROUND_GIA' into _M_ROUND_GIA;
	select value1 from sys_options where trim(option_name) = 'M_ROUND_GIA_NT' into _M_ROUND_GIA_NT;

        _where_dvcs := _where_dvcs || (select * from sys_getrolerecord('{"JSON": {"searchDynamic":{"table_name":"ph64", "user_id":"'|| _user_id ||'", 
                                        "type":"R", "ma_dvcs": "'|| cma_dvcs ||'", "alias": "b" }}}'));
       
 	_where_kho := _where_kho || (select * from sys_getrolerecord('{"JSON": {"searchDynamic":{"table_name":"ct81", "user_id":"'|| _user_id ||'", 
                                        "type":"R", "ma_dvcs": "'|| cma_dvcs ||'", "alias": "a" }}}'));

        -- lấy dữ liệu từ ct64
	strSQL:= 'DROP TABLE IF EXISTS temp_ct64; 
		CREATE TEMP TABLE temp_ct64 AS 
		SELECT 5 AS sysorder, 1 AS sysprint, 1 AS systotal, ''''::ud_ma as ma_ct,
			''''::character varying as ma_dvcs,  a.stt_rec, a.ngay_ct, trim(a.so_ct) as so_ct, 
			''''::character varying as so_ct_hda, ''1900-01-01''::date as ngay_ct_hda,
			''''::character varying as ma_kh, ''''::character varying as ten_kh, 
			a.ma_vt, ''''::character varying as ten_vt,
			a.so_luong, 0::ud_float as so_luong_to2, 0::ud_float as so_luong_to2_cl, a.gia_nt2, a.gia2, a.tien_nt2, a.tien2, 
			''1900-01-01''::date as ngay_gh, ''19000101''::date as ngay_gh_hda, 0::integer as cl_ngay, 
			0::ud_float as so_luong_hda, 0::ud_float as so_luong_cl, a.ln, 
			''''::character varying as so_po, ''''::character varying as so_po_gh, close_yn, sl_rev,
			count(1) over() as total
		FROM ct64 a
		WHERE 1=1
		and exists ( select 1 from ph64 b where a.stt_rec = b.stt_rec
			and b.status <> ''0'' and status <> ''15''
			AND (CASE WHEN '''||cstatus||''' <> ''*'' THEN case when '''||cstatus||''' = '''' then true else b.status = any(string_to_array('''||cstatus||''', '','')) end ELSE 1=1 END) 
			and b.ngay_ct between '''|| dfrom ||''' and (case when '''||dto||''' = ''1900-01-01'' then current_date else '''||dto||''' end)
			and case when '''||cso_ct1||''' <> '''' then b.so_ct >= '''||cso_ct1||''' else 1=1 end
			and case when '''||cso_ct2||''' <> '''' then b.so_ct <= '''||cso_ct2||''' else 1=1 end
			and case when '''||cma_kh||''' = '''' then true else b.ma_kh = any(string_to_array('''||cma_kh||''', '','')) end
			and case when '''||cma_dvcs||''' = '''' then true else b.ma_dvcs = any(string_to_array('''||cma_dvcs||''', '','')) end
			AND case when '||quote_literal(cma_nvbh)||' = '''' then true else ma_nvbh = any(string_to_array('||quote_literal(cma_nvbh)||', '','')) end
			'|| _where_dvcs ||'
		)
		and case when ('||quote_literal(cnh_vt1)||' <> '''' 
				or '||quote_literal(cnh_vt2)||' <> '''' 
				or '||quote_literal(cnh_vt3)||' <> ''''  
				or '||quote_literal(cnh_vt4)||' <> '''' 
				or '||quote_literal(cnh_vt5)||' <> '''' 
				or '||quote_literal(cloai_vt)||' <> '''')
			then exists (select 1 from dmvt c where a.ma_vt = c.ma_vt
				and case when '''||cnh_vt1||''' = '''' then true else nh_vt1 = any(string_to_array('''||cnh_vt1||''', '','')) end  
				and case when '''||cnh_vt2||''' = '''' then true else nh_vt2 = any(string_to_array('''||cnh_vt2||''', '','')) end  
				and case when '''||cnh_vt3||''' = '''' then true else nh_vt3 = any(string_to_array('''||cnh_vt3||''', '','')) end  
				and case when '''||cnh_vt4||''' = '''' then true else nh_vt4 = any(string_to_array('''||cnh_vt4||''', '','')) end  
				and case when '''||cnh_vt5||''' = '''' then true else nh_vt5 = any(string_to_array('''||cnh_vt5||''', '','')) end
				and case when '''||cloai_vt||''' = '''' then true else ma_loai_vt = any(string_to_array('''||cloai_vt||''', '','')) end
				)
			else 1=1 end
		AND case when '''||cma_kho||''' = '''' then true else a.ma_kho = any(string_to_array('''||cma_kho||''', '','')) end
		AND case when '''||cma_vt||''' = '''' then true else a.ma_vt = any(string_to_array('''||cma_vt||''', '','')) end
		AND case when '''||ctk_dt||''' = '''' then true else a.tk_dt = any(string_to_array('''||ctk_dt||''', '','')) end
		AND case when '''||ctk_vt||''' = '''' then true else a.tk_vt = any(string_to_array('''||ctk_vt||''', '','')) end
		AND case when '''||cma_vv||''' = '''' then true else a.ma_vv = any(string_to_array('''||cma_vv||''', '','')) end
		and case when a.ma_kho <> '''' then 1=1 '||_where_kho||' else 1=1 end ';
                               
	RAISE NOTICE 'strSQL = %', strSQL;
	EXECUTE strSQL;

	-- select * from temp_ct64
	-- update thông tin đơn hàng
	update temp_ct64 a set ma_kh = b.ma_kh, ma_dvcs = b.ma_dvcs, ngay_ct = b.ngay_ct, so_ct = b.so_ct, ma_ct = b.ma_ct, so_po = b.so_po
	from ph64 b where a.stt_rec = b.stt_rec;

	update temp_ct64 a set ten_kh = b.ten_kh from dmkh b where a.ma_kh = b.ma_kh;
	update temp_ct64 a set ten_vt = b.ten_vt from dmvt b where a.ma_vt = b.ma_vt;

	
	
	-- bảng chi tiết giao hàng của đơn hàng
	strSQL:= 'DROP TABLE IF EXISTS temp_kq; 
	create temp table temp_kq as
	SELECT 5 AS sysorder, 1 AS sysprint, 0 AS systotal, 0 as stt, 
		''''::character varying as ma_dvcs,  ''''::ud_ma as ma_ct, a.stt_rec, ''1900-01-01''::ud_ngay as ngay_ct, ''''::character varying as so_ct, 
		''''::character varying as so_ct_hda, ''1900-01-01''::date as ngay_ct_hda,
		''''::character varying as ma_kh, ''''::character varying as ten_kh, 
		a.ma_vt, ''''::character varying as ten_vt,
		sum(a.so_luong) as so_luong, 0::ud_float as so_luong_to2, 0::ud_float as so_luong_to2_cl, 0::ud_float gia_nt2, 0::ud_float as gia2, 0::ud_float as tien_nt2, 0::ud_float as tien2, 
		a.ngay_gh, ''19000101''::date as ngay_gh_hda, 0::integer as cl_ngay, 
		0::ud_float as so_luong_hda, 0::ud_float as so_luong_cl, ''''::character varying as status, a.ln, a.ln_item as ln_so1, 
		''''::character varying as so_po, so_po as so_po_gh, count(1) over() as total, 0::ud_float sl_close, '''':: character varying status_name, 0::ud_float sl_rev, 0::ud_smallint close_yn
	from ctkhgh a 
	where exists (select 1 from temp_ct64 b where a.stt_rec = b.stt_rec)
	and case when ('||quote_literal(cnh_vt1)||' <> '''' 
				or '||quote_literal(cnh_vt2)||' <> '''' 
				or '||quote_literal(cnh_vt3)||' <> ''''  
				or '||quote_literal(cnh_vt4)||' <> '''' 
				or '||quote_literal(cnh_vt5)||' <> '''' 
				or '||quote_literal(cloai_vt)||' <> '''')
			then exists (select 1 from dmvt c where a.ma_vt = c.ma_vt
				and case when '''||cnh_vt1||''' = '''' then true else nh_vt1 = any(string_to_array('''||cnh_vt1||''', '','')) end  
				and case when '''||cnh_vt2||''' = '''' then true else nh_vt2 = any(string_to_array('''||cnh_vt2||''', '','')) end  
				and case when '''||cnh_vt3||''' = '''' then true else nh_vt3 = any(string_to_array('''||cnh_vt3||''', '','')) end  
				and case when '''||cnh_vt4||''' = '''' then true else nh_vt4 = any(string_to_array('''||cnh_vt4||''', '','')) end  
				and case when '''||cnh_vt5||''' = '''' then true else nh_vt5 = any(string_to_array('''||cnh_vt5||''', '','')) end
				and case when '''||cloai_vt||''' = '''' then true else ma_loai_vt = any(string_to_array('''||cloai_vt||''', '','')) end
				)
			else 1=1 end
		AND case when '''||cma_vt||''' = '''' then true else a.ma_vt = any(string_to_array('''||cma_vt||''', '','')) end
	group by a.stt_rec, a.ma_vt, a.ngay_gh, a.ln, a.ln_item';
	RAISE NOTICE 'strSQL = %', strSQL;
	EXECUTE strSQL;


	
	-- select  * from temp_ct64
	
	update temp_kq a set ngay_ct = b.ngay_ct, ma_ct = b.ma_ct, so_ct = b.so_ct, ma_kh = b.ma_kh, ten_kh = b.ten_kh, ma_vt = b.ma_vt, ten_vt = b.ten_vt,
			gia_nt2 = b.gia_nt2, gia2 = b.gia2, tien_nt2 = b.tien_nt2, tien2 = b.tien2, so_po = b.so_po, close_yn = b.close_yn, sl_rev = b.sl_rev
		from temp_ct64 b where a.stt_rec = b.stt_rec and a.ln_so1 = b.ln;
	
	-- update temp_kq 
        -- bảng tạm lệnh giao hàng
        -- select * from temp_ct96
	DROP TABLE IF EXISTS temp_ct96;
	CREATE TEMP TABLE temp_ct96 AS
	select a.ma_vt, a.stt_rec as stt_rec_so1, a.ln, 0 as ln_so1, sum(so_luong) as so_luong
	from(
		SELECT 	a.ma_vt, stt_rec_so1 as stt_rec, case when ln_so1 = 0 then ln_so1_goc else ln_so1 end as ln, so_luong
		FROM ctkhgh a
		WHERE 1=1
			AND ma_ct = 'TO2'
			AND exists (select 1 from ph96 b where a.stt_rec = b.stt_rec and status in ('1', '11', '12') )
			and exists (select 1 from temp_ct64 b where a.stt_rec_so1 = b.stt_rec)
		-- union all
-- 
-- 		SELECT 	a.ma_vt, stt_rec_so1_goc as stt_rec, case when ln_so1 = 0 then ln_so1_goc else ln_so1 end as ln, so_luong
-- 		FROM ctkhgh a
-- 		WHERE 1=1
-- 			AND ma_ct = 'TO2'
-- 			AND exists (select 1 from ph96 b where a.stt_rec = b.stt_rec and status in ('1', '11', '12') )
-- 			and exists (select 1 from temp_ct64 b where a.stt_rec_so1_goc = b.stt_rec)
	)a
	GROUP BY a.ma_vt, stt_rec, ln;
		

	
	-- bảng tạm hóa đơn bán hàng
	-- select * from temp_ct81
	DROP TABLE IF EXISTS temp_ct81;
	CREATE TEMP TABLE temp_ct81 AS
	SELECT 	a.ma_vt, max(a.ngay_ct) as ngay_gh, case when coalesce(stt_rec_so1, '') = '' then stt_rec_so1_goc else stt_rec_so1 end as stt_rec_so1, 
		case when ln_so1 = 0 then ln_so1_goc else ln_so1 end as ln,
		0 as ln_so1,
		max(ngay_ct) as ngay_ct, min(so_ct) as so_ct,
		sum(so_luong) as so_luong
	FROM ct81 a
	WHERE 1=1
		AND stt_rec in(select stt_rec from ph81 where status != '0' and status <> '15')
		and (exists (select 1 from temp_ct64 b where a.stt_rec_so1 = b.stt_rec)
			--or exists (select 1 from temp_ct64 b where a.stt_rec_so1_goc = b.stt_rec)
		)
	GROUP BY a.ma_vt, case when coalesce(stt_rec_so1, '') = '' then stt_rec_so1_goc else stt_rec_so1 end, 
		case when ln_so1 = 0 then ln_so1_goc else ln_so1 end;

	--/*
	--update temp_ct81 a set ln_so1 = b.ln_item from ctkhgh b where a.stt_rec_so1 = b.stt_rec or a.stt_rec_so1 = b.stt_rec_so1_goc or a.stt_rec_so1 = b.stt_rec_so1;
	-- select stt_rec, ln, ma_vt, so_luong_hda, * from temp_kq
	-- select * from ctkhgh
	-- update lịch giao hàng

        update temp_kq a set so_luong_to2 = b.so_luong from temp_ct96 b where a.stt_rec = b.stt_rec_so1 and a.ln = b.ln and a.ma_vt = b.ma_vt;
		
        
	update temp_kq a set ngay_ct_hda = b.ngay_ct, so_ct_hda = b.so_ct, 
			ngay_gh_hda = b.ngay_gh, so_luong_hda = b.so_luong
		from temp_ct81 b where a.stt_rec = b.stt_rec_so1 and a.ln = b.ln and a.ma_vt = b.ma_vt;
		
	update temp_kq a set so_luong_to2_cl = so_luong - so_luong_to2, so_luong_cl = so_luong - so_luong_hda, cl_ngay = a.ngay_gh - a.ngay_gh_hda;
	update temp_kq a set sl_close = so_luong - so_luong_hda where close_yn = 1;
	update temp_kq a set sl_close = so_luong - so_luong_hda where exists(select 1 from ph64 b where a.stt_rec = b.stt_rec and status = '13' );
	update temp_kq a set so_luong_cl = so_luong_cl - sl_close;
	update temp_kq a set so_luong_cl = 0 where exists (select 1 from ph64 b where a.stt_rec = b.stt_rec and status = '14');
	-- update temp_kq a set so_luong_to2 = a.so_luong_to2 + b.sum_sl_to2, so_luong_to2_cl = a.so_luong_to2_cl - sum_sl_to2, so_luong_cl = a.so_luong_cl - b.sum_sl_hda
-- 	from (select so_po_gh, sum(so_luong_to2) sum_sl_to2, sum(so_luong_hda) sum_sl_hda from temp_kq  a where exists(select 1 from ph64 b where a.stt_rec = b.stt_rec and status = '13') group by  so_po_gh) b
-- 	where a.so_po_gh = b.so_po_gh and a.sl_close <> 0;

	drop table if exists temp_status;
	create temp table temp_status as
	select * from sys_languages_data where form = 'TT_DH' and culture = cculture;
	 
	update temp_kq a set status = (select b.value from temp_status b where b.name = 'chua_den_han') where a.ngay_gh > current_date;
	update temp_kq a set status = (select b.value from temp_status b where b.name = 'chua_giao') where a.ngay_gh_hda = '1900-01-01';
	update temp_kq a set status = (select b.value from temp_status b where b.name = 'truoc_han') where a.ngay_gh_hda < a.ngay_gh and a.ngay_gh_hda <> '19000101'::ud_ngay;
	update temp_kq a set status = (select b.value from temp_status b where b.name = 'giao_muon') where a.ngay_gh_hda > a.ngay_gh;
	update temp_kq a set status = (select b.value from temp_status b where b.name = 'dung_han') where a.ngay_gh_hda = a.ngay_gh;

	--*/
	--select name, b.value from sys_languages_data b where b.culture = 'vi-VN' and b.form = 'TT_DH' and b.name in( 'chua_den_han','cham_giao','truoc_han','giao_muon','dung_han' )

	-- thêm dòng nhóm theo đơn hàng
	if(cgroup <> '0') then 
		insert into temp_kq(sysorder, sysprint, systotal, stt_rec, ma_ct, so_ct, ngay_ct, ten_vt, so_luong, so_luong_to2, so_luong_to2_cl, tien2, so_luong_hda, so_luong_cl, sl_close)
		select 3, 0, 1, stt_rec, max(ma_ct), max(so_ct), max(ngay_ct),
		max(ten_kh), 
		sum(so_luong), sum(so_luong_to2), sum(so_luong_to2_cl), sum(tien2), sum(so_luong_hda), sum(so_luong_cl), sum(sl_close)
		from temp_kq 
		where systotal = 0
		group by stt_rec;

		update temp_kq a set status_name = b.status from ph64 b where a.stt_rec = b.stt_rec and sysorder = 3;
		update  temp_kq a set status_name = b.statusname from (select * from sys_dmtt where ma_ct = 'SO1') b where a.status_name = b.status and sysorder = 3;
	end if;
	
	
	-- thêm dòng tổng cộng
	insert into temp_kq(sysorder, sysprint, systotal, stt_rec, ten_vt, so_luong, so_luong_to2, so_luong_to2_cl, tien2, so_luong_hda, so_luong_cl, total)
	select 0, 0, 1, '',
	(select b.value from sys_languages_data b where b.culture = cculture and b.form = 'TT_BCBK' and b.name = 'tong_cong'), 
	sum(so_luong), sum(so_luong_to2), sum(so_luong_to2_cl), sum(tien2), sum(so_luong_hda), sum(so_luong_cl), max(total)
	from temp_kq 
	where systotal = 0;

	
	-- thêm dòng tổng cộng chưa giao
	insert into temp_kq(sysorder, sysprint, systotal, stt_rec, ten_vt, so_luong, tien2, so_luong_hda, so_luong_cl)
	select 1, 0, 1, '00',
	(select b.value from sys_languages_data b where b.culture = cculture and b.form = 'POStatus' and b.name = 'T_SL_CHUAGIAO'), 
	sum(so_luong), sum(tien2), sum(so_luong_hda), sum(so_luong_cl)
	from temp_kq 
	where systotal = 0 and so_ct_hda = '';

	-- thêm dòng tổng cộng dh theo kế hoạch
	insert into temp_kq(sysorder, sysprint, systotal, stt_rec, ten_vt, so_luong, tien2, so_luong_hda, so_luong_cl)
	select 1, 0, 1, '01',
	(select b.value from sys_languages_data b where b.culture = cculture and b.form = 'POStatus' and b.name = 'T_SL_GIAOKH'), 
	sum(so_luong), sum(tien2), sum(so_luong_hda), sum(so_luong_cl)
	from temp_kq 
	where systotal = 0 and so_ct_hda <> '' and so_luong_cl = 0;

	-- thêm dòng tổng cộng dh VƯỢT kẾ HOẠCH
	insert into temp_kq(sysorder, sysprint, systotal, stt_rec, ten_vt, so_luong, tien2, so_luong_hda, so_luong_cl)
	select 1, 0, 1, '02',
	(select b.value from sys_languages_data b where b.culture = cculture and b.form = 'POStatus' and b.name = 'T_SL_VUOTKH'),
	sum(so_luong), sum(tien2), sum(so_luong_hda), sum(so_luong_cl)
	from temp_kq 
	where systotal = 0 and so_ct_hda <> '' and ngay_gh_hda < ngay_gh and so_luong_cl < 0;
	
	-- thêm dòng tổng cộng dh CHẬM kẾ HOẠCH
	insert into temp_kq(sysorder, sysprint, systotal, stt_rec, ten_vt, so_luong, tien2, so_luong_hda, so_luong_cl)
	select 1, 0, 1, '03',
	(select b.value from sys_languages_data b where b.culture = cculture and b.form = 'POStatus' and b.name = 'T_SL_CHAMKH'),
	sum(so_luong), sum(tien2), sum(so_luong_hda), sum(so_luong_cl)
	from temp_kq 
	where systotal = 0 and so_ct_hda <> '' and so_luong_cl > 0;

	update temp_kq set ngay_gh = null where ngay_gh = '1900-01-01' or ngay_gh = '0001-01-01';
	update temp_kq set ngay_ct = null where ngay_ct = '1900-01-01' or ngay_ct = '0001-01-01';
	update temp_kq set ngay_gh_hda = null where ngay_gh_hda = '1900-01-01' or ngay_gh_hda = '0001-01-01';
	update temp_kq set ngay_ct_hda = null where ngay_ct_hda = '1900-01-01' or ngay_ct_hda = '0001-01-01';
	
	FOR r IN SELECT * FROM temp_kq ORDER BY stt_rec, sysorder
	LOOP
		if r.sysorder = 0 or r.sysorder = 1 then 
			r.stt_rec = null;
			r.ngay_ct = null;
			r.ngay_gh = null;
		end if;
		if r.sysorder = 3 then
			_stt = 0;
		end if;
		if r.sysorder = 5 and cgroup <> '0' then
			r.so_ct = '';
			r.ngay_ct = null;
			r.ma_dvcs = null;
			_stt = _stt + 1;
			
		end if;
		r.stt = _stt;
		RETURN NEXT r;
	END LOOP;
	RETURN;
	
    --DROP TABLE tmp0;
    --DROP TABLE temp_kq;

    /*
     select * from sobctiendogh('{"JSON":{"user_id":"1","searchDynamic":
     {"dfrom":"2021-06-01","dto":"2021-12-07","cso_ct1":"","cso_ct2":"","cma_kh":"","cma_kho":"","cma_vt":"","cnh_vt1":"","cnh_vt2":"","cnh_vt3":"","cnh_vt4":"","cnh_vt5":"","cma_dvcs":"001","mau_bc":"001","gridid":"SOBCTienDoGH","culture":"vi-VN"}
      }}')
     
   */
       
END
$function$
