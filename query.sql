SELECT *
FROM (
    SELECT DISTINCT ON (cr."pre_user_id")

      cr."pre_user_id" AS "Pre User ID",

      plu."name"
        AS "Pre Login Leap User - Pre User → Name",

      plu."phone"
        AS "Pre Login Leap User - Pre User → Phone",

      cr."has_attended"
        AS "Counselor Assigned",

      cr."has_attended"
        AS "has_attended",

      cr."reschedule_id"
        AS "reschedule_id",

      (
        cr."created_at"
        AT TIME ZONE 'UTC'
        AT TIME ZONE 'Asia/Kolkata'
      ) AS "Created At IST",

      cr."form_id"
        AS "Form ID",

      (
        cs."start_date_time"
        AT TIME ZONE 'UTC'
        AT TIME ZONE 'Asia/Kolkata'
      ) AS "Slot Time in IST",

      cs."region"
        AS "Region",

      r."name"
        AS "meeting_region",

      plu."utm_source"
        AS "Pre Login Leap User - Pre User → Utm Source",

      plu."utm_campaign"
        AS "Pre Login Leap User - Pre User → Utm Campaign",

      apd."call_completed"
        AS "Call Completion",

      ABS(
        ROUND(
          (
            EXTRACT(
              EPOCH FROM (
                (
                  cs."start_date_time"
                  AT TIME ZONE 'UTC'
                  AT TIME ZONE 'Asia/Kolkata'
                ) - (
                  cr."created_at"
                  AT TIME ZONE 'UTC'
                  AT TIME ZONE 'Asia/Kolkata'
                )
              )
            ) / 86400
          )::numeric,
          0
        )
      )::int AS "Difference Between Slot Booking And Lead Date (Days)"

    FROM
      "public"."counselling_registration" cr

    LEFT JOIN "public"."counselling_slot" cs
      ON cr."counselling_slot_id" = cs."id"

    LEFT JOIN "public"."pre_login_leap_user" plu
      ON cr."pre_user_id" = plu."id"

    LEFT JOIN "public"."qe_user_city_state" qucs
      ON cr."pre_user_id" = qucs."pre_user_id"

    LEFT JOIN "public"."region" r
      ON qucs."region_id" = r."id"

    LEFT JOIN (
        SELECT DISTINCT ON ("pre_user_id")
            "pre_user_id",
            "call_completed",
            "created_at"
        FROM "public"."airo_profiling_discussion"
        ORDER BY
            "pre_user_id",
            "created_at" DESC
    ) apd
      ON cr."pre_user_id" = apd."pre_user_id"

    WHERE
      cs."is_delete" = FALSE

      AND cr."form_id" = 'Profiling_Study_Plan_Registration'

      AND cs."slot_type" = 2

      [[AND DATE(
        (
          cr."created_at"
          AT TIME ZONE 'UTC'
          AT TIME ZONE 'Asia/Kolkata'
        )
      ) >= {{start_date}}]]

      [[AND DATE(
        (
          cr."created_at"
          AT TIME ZONE 'UTC'
          AT TIME ZONE 'Asia/Kolkata'
        )
      ) <= {{end_date}}]]

      [[AND cr."has_attended" = CAST({{has_attended}} AS BOOLEAN)]]

      [[AND CAST(apd."call_completed" AS TEXT)
      ILIKE CONCAT('%', {{call_completed}}, '%')]]

      [[AND ABS(
        ROUND(
          (
            EXTRACT(
              EPOCH FROM (
                (
                  cs."start_date_time"
                  AT TIME ZONE 'UTC'
                  AT TIME ZONE 'Asia/Kolkata'
                ) - (
                  cr."created_at"
                  AT TIME ZONE 'UTC'
                  AT TIME ZONE 'Asia/Kolkata'
                )
              )
            ) / 86400
          )::numeric,
          0
        )
      )::int >= {{min_difference_days}}]]

      [[AND ABS(
        ROUND(
          (
            EXTRACT(
              EPOCH FROM (
                (
                  cs."start_date_time"
                  AT TIME ZONE 'UTC'
                  AT TIME ZONE 'Asia/Kolkata'
                ) - (
                  cr."created_at"
                  AT TIME ZONE 'UTC'
                  AT TIME ZONE 'Asia/Kolkata'
                )
              )
            ) / 86400
          )::numeric,
          0
        )
      )::int <= {{max_difference_days}}]]

    ORDER BY
      cr."pre_user_id",
      cr."created_at" DESC
) latest_records

ORDER BY "Created At IST" DESC

LIMIT 1048575;

