-- TrainAssociatedService

ALTER TABLE AssociatedService RENAME TO TrainAssociatedService;

-- AssociatedType

ALTER TABLE AssociatedType RENAME TO TrainAssociatedServiceType;

-- Brand

ALTER TABLE Brand RENAME TO TrainBrand;

-- Call

ALTER TABLE Call RENAME TO TrainCall;

-- Leg

ALTER TABLE Leg RENAME TO TrainLeg;

-- LegCall

ALTER TABLE LegCall RENAME TO TrainLegCall;

-- Operator

ALTER TABLE Operator RENAME TO TrainOperator;

-- OperatorCode

ALTER TABLE OperatorCode RENAME TO TrainOperatorCode;

-- OperatorStock

ALTER TABLE OperatorStock RENAME TO TrainOperatorStock;

-- Service

ALTER TABLE Service RENAME TO TrainService;

-- ServiceEndpoint

-- Station

ALTER TABLE Station RENAME TO TrainStation;

-- StationName

ALTER TABLE StationName RENAME TO TrainStationName;

-- StationPoint

ALTER TABLE StationPoint RENAME TO TrainStationPoint;

-- Stock

ALTER TABLE Stock RENAME TO TrainStock;

-- StockFormation

ALTER TABLE StockFormation RENAME TO TrainStockFormation;

-- StockReport

ALTER TABLE StockReport RENAME TO TrainStockReport;

-- StockSegment

ALTER TABLE StockSegment RENAME TO TrainStockSegment;

-- StockSegmentReport

ALTER TABLE StockSegmentReport RENAME TO TrainStockSegmentReport;

-- StockSubclass

ALTER TABLE StockSubclass RENAME TO TrainStockSubclass;