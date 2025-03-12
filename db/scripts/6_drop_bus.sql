CREATE OR REPLACE FUNCTION DropBusTables ()
RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    DROP TABLE BusLeg;
    DROP FUNCTION CallsAreSameJourney;
    DROP TABLE BusVehicle;
    DROP TABLE BusModel;
    DROP TABLE BusCall;
    DROP TABLE BusJourney;
    DROP TABLE BusServiceVia;
    DROP TABLE BusService;
    DROP TABLE BusOperator;
    DROP TABLE BusStop;
END;
$$;

CREATE OR REPLACE FUNCTION DropBusTypes ()
RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    DROP TYPE BusLegInData;
    DROP TYPE BusJourneyInData;
    DROP TYPE BusCallInData;
    DROP TYPE BusVehicleOutData;
    DROP TYPE BusVehicleInData;
    DROP TYPE BusModelInData;
    DROP TYPE BusServiceViaOutData;
    DROP TYPE BusServiceOutData;
    DROP TYPE BusServiceViaInData;
    DROP TYPE BusServiceInData;
    DROP TYPE BusOperatorOutData;
    DROP TYPE BusOperatorInData;
    DROP TYPE BusStopOutData;
    DROP TYPE BusStopInData;
END;
$$;

CREATE OR REPLACE FUNCTION DropBusInsertFunctions ()
RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    DROP FUNCTION InsertBusStops;
    DROP FUNCTION InsertBusOperators;
    DROP FUNCTION InsertBusServices;
    DROP FUNCTION InsertBusServiceVias;
    DROP FUNCTION InsertTransXChangeBusData;
    DROP FUNCTION InsertBusModels;
    DROP FUNCTION InsertBusVehicles;
    DROP FUNCTION InsertBusModelsAndVehicles;
    DROP FUNCTION InsertBusCalls;
    DROP FUNCTION InsertBusJourney;
    DROP FUNCTION GetBusCallIdFromJourneyCallIndex;
    DROP FUNCTION InsertBusLeg;
END;
$$;

CREATE OR REPLACE FUNCTION DropBusSelectFunctions ()
RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    DROP FUNCTION GetBusStops;
    DROP FUNCTION GetBusStopsFromAtcos;
    DROP FUNCTION GetBusOperators;
    DROP FUNCTION GetBusOperatorsByName;
    DROP FUNCTION GetBusOperatorsByNationalOperatorCode;
    DROP FUNCTION GetBusServiceVias;
    DROP FUNCTION GetBusServices;
    DROP FUNCTION GetBusServicesByOperatorId;
    DROP FUNCTION GetBusServicesByNationalOperatorCode;
    DROP FUNCTION GetBusServicesByOperatorName;
    DROP FUNCTION GetBusVehicle;
END;
$$;

CREATE OR REPLACE FUNCTION DropBusData ()
RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    PERFORM DropBusSelectFunctions();
    PERFORM DropBusInsertFunctions();
    PERFORM DropBusTypes();
    PERFORM DropBusTables();
END;
$$;