DROP VIEW IF EXISTS transport_user_bus_leg_summary_view;

CREATE OR REPLACE VIEW transport_user_bus_leg_summary_view
AS
SELECT
    transport_user_bus_leg.user_id,
    bus_leg_summary_view.bus_leg_id,
    bus_leg_summary_view.operator,
    bus_leg_summary_view.services,
    bus_leg_summary_view.vehicle,
    bus_leg_summary_view.board_stop,
    bus_leg_summary_view.alight_stop,
    bus_leg_summary_view.duration
FROM bus_leg_summary_view
INNER JOIN transport_user_bus_leg
ON bus_leg_summary_view.bus_leg_id = transport_user_bus_leg.bus_leg_id;