import pandas as pd
import matplotlib.pyplot as plt
import gc
################
# DATA READING #
################

train = pd.read_csv("interbank-internacional-2019/ib_base_inicial_train/ib_base_inicial_train.csv")
X_test = pd.read_csv("interbank-internacional-2019/ib_base_inicial_test/ib_base_inicial_test.csv")

sunat = pd.read_csv("interbank-internacional-2019/ib_base_sunat/ib_base_sunat.csv")
reniec = pd.read_csv("interbank-internacional-2019/ib_base_reniec/ib_base_reniec.csv")
vehicular = pd.read_csv("interbank-internacional-2019/ib_base_vehicular/ib_base_vehicular.csv")

campanias = pd.read_csv("interbank-internacional-2019/data_generation/campanias_new_3.csv", encoding='latin-1')
digital = pd.read_csv("interbank-internacional-2019/data_generation/digital_final.csv", encoding='latin-1')
rcc = pd.read_csv("interbank-internacional-2019/data_generation/rcc_historia_persona.csv", encoding='latin-1')

#
# Target Binary
#

y_train = train[['codmes', 'id_persona', 'margen']].copy()
y_train["prediction_id"] = y_train["id_persona"].astype(str) + "_" + y_train["codmes"].astype(str)
# y_train["target"] = (y_train["margen"] > 0).astype(int)
y_train = y_train.set_index("prediction_id")
X_train = train.drop(["margen"], axis=1)
X_train["prediction_id"] = X_train["id_persona"].astype(str) + "_" + X_train["codmes"].astype(str)
del train

X_train["ratio"] = X_train["linea_ofrecida"] / X_train["ingreso_neto"]
X_test["ratio"] = X_test["linea_ofrecida"] / X_test["ingreso_neto"]

#
# id_persona
#

sunat = sunat.groupby(["id_persona", "activ_econo"]).meses_alta.sum().unstack(level=1, fill_value=0).astype("int32")
vehicular1 = vehicular.groupby(["id_persona", "marca"]).veh_var1.sum().unstack(level=1, fill_value=0).astype("float32")
vehicular2 = vehicular.groupby(["id_persona", "marca"]).veh_var2.sum().unstack(level=1, fill_value=0).astype("float32")
reniec = reniec.set_index("id_persona").astype("float32")
del vehicular

vehicular1.columns = [c + "_v1" for c in vehicular1.columns]
vehicular2.columns = [c + "_v2" for c in vehicular2.columns]

X_train = X_train.set_index("prediction_id").astype("int32").reset_index().set_index("id_persona").join(vehicular1).join(vehicular2).join(reniec).join(sunat)
X_test = X_test.set_index("prediction_id").astype("int32").reset_index().set_index("id_persona").join(vehicular1).join(vehicular2).join(reniec).join(sunat)
del vehicular1, vehicular2, reniec, sunat

#
# Digital
#


meses = {
    201901: slice(201800, 201904),
    201902: slice(201800, 201904),
    201903: slice(201800, 201904),
    201904: slice(201800, 201904),
    201905: slice(201800, 201904),
    201906: slice(201800, 201904),
    201907: slice(201800, 201904)
}

digital = digital.reset_index().set_index(["id_persona", "codmes"]).astype("float32")

print("X_train join digital")
X_train = X_train.reset_index().join(digital, on=["id_persona", "codmes"]).set_index("prediction_id")
gc.collect()

print("X_test join digital")
X_test = X_test.reset_index().join(digital, on=["id_persona", "codmes"]).set_index("prediction_id")
gc.collect()

del digital
gc.collect()

#
# RCC
#
'''
complementos = []
for mes in meses.keys():
    print("*"*10, mes, "*"*10)
    res = pd.concat([
        rcc.loc[meses[mes]].groupby("id_persona").sum()        
    ], axis=1)
    res["codmes"] = mes
    res = res.reset_index().set_index(["id_persona", "codmes"]).astype("float32")
    complementos.append(res)

del rcc
gc.collect()
'''
rcc = rcc.set_index("id_persona").astype("float32")

print("X_train join RCC")
X_train = X_train.reset_index().join(rcc, on=["id_persona"]).set_index("prediction_id")
gc.collect()

print("X_test joing RCC")
X_test = X_test.reset_index().join(rcc, on=["id_persona"]).set_index("prediction_id")

del rcc
gc.collect()

#
# Campanias
#

print("X_train join campanias")
X_train = X_train.reset_index().merge(campanias, on=["id_persona", "codmes"], how="left").set_index("prediction_id")
gc.collect()

print("X_test join campanias")
X_test = X_test.reset_index().merge(campanias, on=["id_persona", "codmes"], how="left").set_index("prediction_id")
gc.collect()

del campanias
gc.collect()

#
# Removing Non ASCII characters
#

non_ascii = X_train.columns[[not all(ord(c) < 128 for c in s) for s in X_train.columns]].tolist()
non_ascii

for i, c in enumerate(non_ascii):
    X_train["non_ascii_" + str(i)] = X_train[c]
    X_train = X_train.drop(c, axis= 1)
    X_test["non_ascii_" + str(i)] = X_test[c]
    X_test = X_test.drop(c, axis= 1)

X_train.to_csv(r'interbank-internacional-2019/data_generation/train_data_clean.csv')
X_test.to_csv(r'interbank-internacional-2019/data_generation/test_data_clean.csv')
