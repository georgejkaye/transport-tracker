CREATE OR REPLACE FUNCTION InsertBusStops (
    p_stops BusStopInData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusStop (
        atco_code,
        naptan_code,
        stop_name,
        landmark_name,
        street_name,
        crossing_name,
        indicator,
        bearing,
        locality_name,
        parent_locality_name,
        grandparent_locality_name,
        town_name,
        suburb_name,
        latitude,
        longitude
    ) SELECT
        v_stop.atco_code,
        v_stop.naptan_code,
        v_stop.stop_name,
        v_stop.landmark_name,
        v_stop.street_name,
        v_stop.crossing_name,
        v_stop.indicator,
        v_stop.bearing,
        v_stop.locality_name,
        v_stop.parent_locality_name,
        v_stop.grandparent_locality_name,
        v_stop.town_name,
        v_stop.suburb_name,
        v_stop.latitude,
        v_stop.longitude
    FROM UNNEST(p_stops) AS v_stop;
END;
$$;

CREATE OR REPLACE FUNCTION InsertBusOperators (
    p_operators BusOperatorInData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusOperator (
        operator_name,
        national_operator_code
    ) SELECT
        v_operator.operator_name,
        v_operator.national_operator_code
    FROM UNNEST(p_operators) AS v_operator
    ON CONFLICT DO NOTHING;
END;
$$;

CREATE OR REPLACE FUNCTION InsertBusServices (
    p_services BusServiceInData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusService (
        bus_operator_id,
        bods_line_id,
        service_line,
        description_outbound,
        description_inbound
    ) SELECT
        (
            SELECT bus_operator_id
            FROM BusOperator
            WHERE national_operator_code
                = v_service.service_operator_national_code
        ),
        v_service.bods_line_id,
        v_service.service_line,
        v_service.service_outbound_description,
        v_service.service_inbound_description
    FROM UNNEST(p_services) AS v_service
    ON CONFLICT DO NOTHING;
END;
$$;

CREATE OR REPLACE FUNCTION InsertBusServiceVias (
    p_vias BusServiceViaInData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusServiceVia (
        bus_service_id,
        is_outbound,
        via_name,
        via_index
    ) SELECT
        (SELECT bus_service_id
        FROM BusService
        WHERE bods_line_id = v_via.bods_line_id),
        v_via.is_outbound,
        v_via.via_name,
        v_via.via_index
    FROM UNNEST(p_vias) AS v_via
    ON CONFLICT DO NOTHING;
END;
$$;

CREATE OR REPLACE FUNCTION InsertTransXChangeBusData (
    p_services BusServiceInData[],
    p_vias BusServiceViaInData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    PERFORM InsertBusServices(p_services);
    PERFORM InsertBusServiceVias(p_vias);
END;
$$;

CREATE OR REPLACE FUNCTION InsertBusModels (
    p_models BusModelInData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusModel (bus_model_name)
    SELECT v_model.model_name
    FROM UNNEST(p_models) AS v_model
    ON CONFLICT DO NOTHING;
END;
$$;

CREATE OR REPLACE FUNCTION InsertBusVehicles (
    p_vehicles BusVehicleInData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusVehicle (
        operator_id,
        vehicle_number,
        bustimes_id,
        numberplate,
        bus_model_id,
        livery_style,
        operator_name
    )
    SELECT
        v_vehicle.operator_id,
        v_vehicle.vehicle_number,
        v_vehicle.bustimes_id,
        v_vehicle.vehicle_numberplate,
        (SELECT bus_model_id
        FROM BusModel
        WHERE bus_model_name = v_vehicle.vehicle_model),
        v_vehicle.vehicle_livery_style,
        v_vehicle.vehicle_name
    FROM UNNEST(p_vehicles) AS v_vehicle
    ON CONFLICT DO NOTHING;
END;
$$;

CREATE OR REPLACE FUNCTION InsertBusModelsAndVehicles (
    p_models BusModelInData[],
    p_vehicles BusVehicleInData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    PERFORM InsertBusModels(p_models);
    PERFORM InsertBusVehicles(p_vehicles);
END;
$$;

CREATE OR REPLACE FUNCTION InsertBusCalls (
    p_journey_id INT,
    p_calls BusCallInData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusCall (
        bus_journey_id,
        call_index,
        bus_stop_id,
        plan_arr,
        act_arr,
        plan_dep,
        act_dep
    ) SELECT
        p_journey_id,
        v_call.call_index,
        (SELECT bus_stop_id
        FROM BusStop
        WHERE v_call.stop_atco = BusStop.atco_code),
        v_call.plan_arr,
        v_call.act_arr,
        v_call.plan_dep,
        v_call.act_dep
    FROM UNNEST(p_calls) AS v_call;
END;
$$;

CREATE OR REPLACE FUNCTION InsertBusJourney (
    p_journey BusJourneyInData
) RETURNS INT
LANGUAGE plpgsql
AS
$$
DECLARE
    v_journey_id INT;
BEGIN
    INSERT INTO BusJourney (
        bus_service_id,
        bus_vehicle_id
    ) VALUES (p_journey.service_id, p_journey.vehicle_id)
    RETURNING bus_journey_id INTO v_journey_id;
    PERFORM InsertBusCalls(v_journey_id, p_journey.journey_calls);
    RETURN v_journey_id;
END;
$$;

CREATE OR REPLACE FUNCTION InsertBusLeg (
    p_users INT[],
    p_leg BusLegInData
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
DECLARE
    v_journey_id INT;
BEGIN
    SELECT InsertBusJourney(p_leg.journey) INTO v_journey_id;
    INSERT INTO BusLeg (
        user_id,
        bus_journey_id,
        board_call_index,
        alight_call_index
    ) SELECT
        v_user,
        v_journey_id,
        p_leg.board_index,
        p_leg.alight_index
    FROM UNNEST(p_users) AS v_user;
END;
$$;
