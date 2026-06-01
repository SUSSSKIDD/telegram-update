WITH eligible_acd AS (

    SELECT
        pre_user_id,
        created_at,
        source,
        call_completed
    FROM public.airo_call_details
    WHERE is_delete = FALSE
      AND (
            (source = 'WEB_CALL' AND call_completed = 'Yes')
         OR (source = 'WEB_FORM')
      )
),

user_segments AS (

    SELECT
        pre_user_id,
        BOOL_OR(source = 'WEB_CALL') AS has_call,
        BOOL_OR(source = 'WEB_FORM') AS has_form
    FROM eligible_acd
    GROUP BY pre_user_id
),

booking_source AS (

    SELECT
        cr."pre_user_id",

        CASE
            WHEN us.has_call = TRUE AND us.has_form = FALSE
                THEN 'WEB_CALL'

            WHEN us.has_call = FALSE AND us.has_form = TRUE
                THEN 'WEB_FORM'

            WHEN us.has_call = TRUE AND us.has_form = TRUE THEN
                CASE
                    WHEN call_l.call_diff IS NOT NULL
                     AND form_l.form_diff IS NULL THEN 'WEB_CALL'

                    WHEN form_l.form_diff IS NOT NULL
                     AND call_l.call_diff IS NULL THEN 'WEB_FORM'

                    WHEN call_l.call_diff IS NOT NULL
                     AND form_l.form_diff IS NOT NULL THEN
                        CASE
                            WHEN call_l.call_diff <= form_l.form_diff
                                THEN 'WEB_CALL'
                            ELSE 'WEB_FORM'
                        END
                END
        END AS attributed_source

    FROM public.counselling_registration cr

    LEFT JOIN user_segments us
        ON us.pre_user_id = cr."pre_user_id"

    /* nearest WEB_CALL before CR */
    LEFT JOIN LATERAL (
        SELECT
            EXTRACT(EPOCH FROM (cr."created_at" - a.created_at)) AS call_diff
        FROM eligible_acd a
        WHERE a.pre_user_id = cr."pre_user_id"
          AND a.source = 'WEB_CALL'
          AND a.created_at < cr."created_at"
        ORDER BY a.created_at DESC
        LIMIT 1
    ) call_l ON TRUE

    /* nearest WEB_FORM before CR */
    LEFT JOIN LATERAL (
        SELECT
            EXTRACT(EPOCH FROM (cr."created_at" - a.created_at)) AS form_diff
        FROM eligible_acd a
        WHERE a.pre_user_id = cr."pre_user_id"
          AND a.source = 'WEB_FORM'
          AND a.created_at < cr."created_at"
        ORDER BY a.created_at DESC
        LIMIT 1
    ) form_l ON TRUE
)

SELECT *
FROM (

    SELECT DISTINCT ON (cr."pre_user_id")

      cr."pre_user_id" AS "Pre User ID",

      plu."name"
        AS "Pre Login Leap User - Pre User → Name",

      plu."phone"
        AS "Pre Login Leap User - Pre User → Phone",

      cr."has_attended",

      cr."reschedule_id",

      (cr."created_at" AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')
        AS "Created At IST",

      cr."form_id",

      (cs."start_date_time" AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')
        AS "Slot Time in IST",

      cs."region",

      r."name" AS "meeting_region",

      plu."utm_source"
        AS "Pre Login Leap User - Pre User → Utm Source",

      plu."utm_campaign"
        AS "Pre Login Leap User - Pre User → Utm Campaign",

      apd."call_completed"
        AS "Call Completion",

      bs.attributed_source
        AS "Booking Source",

      ABS(
        ROUND(
          (
            EXTRACT(EPOCH FROM (
              (cs."start_date_time" AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')
              -
              (cr."created_at" AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')
            )) / 86400
          )::numeric,
          0
        )
      )::int AS "Difference Between Slot Booking And Lead Date (Days)"

    FROM public.counselling_registration cr

    LEFT JOIN public.counselling_slot cs
      ON cr."counselling_slot_id" = cs."id"

    LEFT JOIN public.pre_login_leap_user plu
      ON cr."pre_user_id" = plu."id"

    LEFT JOIN public.qe_user_city_state qucs
      ON cr."pre_user_id" = qucs."pre_user_id"

    LEFT JOIN public.region r
      ON qucs."region_id" = r."id"

    LEFT JOIN (
        SELECT DISTINCT ON ("pre_user_id")
            "pre_user_id",
            "call_completed",
            "created_at"
        FROM public.airo_profiling_discussion
        ORDER BY "pre_user_id", "created_at" DESC
    ) apd
      ON cr."pre_user_id" = apd."pre_user_id"

    LEFT JOIN booking_source bs
      ON cr."pre_user_id" = bs.pre_user_id

    WHERE
      cs."is_delete" = FALSE
      AND cr."form_id" = 'Profiling_Study_Plan_Registration'
      AND cs."slot_type" = 2

      [[AND DATE(
        cr."created_at" AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'
      ) >= {{start_date}}]]

      [[AND DATE(
        cr."created_at" AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'
      ) <= {{end_date}}]]

      [[AND cr."has_attended" = CAST({{has_attended}} AS BOOLEAN)]]

      [[AND CAST(apd."call_completed" AS TEXT)
      ILIKE CONCAT('%', {{call_completed}}, '%')]]

      [[AND ABS(
        ROUND(
          (
            EXTRACT(EPOCH FROM (
              cs."start_date_time" AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'
              -
              cr."created_at" AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'
            )) / 86400
          )::numeric,
          0
        )
      )::int >= {{min_difference_days}}]]

      [[AND ABS(
        ROUND(
          (
            EXTRACT(EPOCH FROM (
              cs."start_date_time" AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'
              -
              cr."created_at" AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'
            )) / 86400
          )::numeric,
          0
        )
      )::int <= {{max_difference_days}}]]

    ORDER BY
      cr."pre_user_id",
      cr."created_at" DESC

) latest_records

WHERE 1 = 1

[[AND latest_records."Booking Source" = {{booking_source}}]]

ORDER BY "Created At IST" DESC

LIMIT 1048575;