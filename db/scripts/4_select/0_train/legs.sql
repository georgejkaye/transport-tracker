DROP VIEW transport_user_train_leg_view;

CREATE OR REPLACE VIEW transport_user_train_leg_view AS
SELECT
    transport_user_train_leg.user_id,
    train_leg.train_leg_id
FROM transport_user_train_leg
INNER JOIN train_leg
ON transport_user_train_leg.train_leg_id = train_leg.train_leg_id
INNER JOIN (
    SELECT
        train_leg.train_leg_id,
        ARRAY_AGG((

        )::)

) transport_user_train_leg_service_view
ON train_leg.train_leg_id = transport_user_train_leg_service_view.train_leg_id



DROP FUNCTION select_legs_by_id (
    p_leg_ids INTEGER[]
)