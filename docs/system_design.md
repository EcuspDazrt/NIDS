```mermaid
graph TD
	A(Network Sniffer)
	B(Sort packet data into flows)
	C(Extract features from flows)
	D(Store current feature state in Redis)
	E(Pass through Models)
	F(Random Forest)
	G(Neural Network)
    H(Normalize predictions with a risk aggregator)
	I(Store logs in SQLite)
	J(Pass to Dashboard)
	K(Send alert if danger passes threshold)
	L(Offline nn training)
    A --> B --> C --> D --> E --> F
	E --> G
	G --> H
	F --> H --> I --> J --> K --> L --> G