from utils.constants import RCL_FIELD


def queryEntityDetails():
    query = f"""
    SELECT 
        * 
    FROM
        entityconsdetails
    WHERE
        entitytype!='ORGANIZACAO'
    ORDER BY
        entityid    
    """
    
    return query

def queryAdjusteQueue(idEntity):
    
    query = f"""
    WITH refdateTable AS (
        SELECT DISTINCT
            queue.refdate AS Refdate
        FROM 
            queue
        WHERE
            queue.entity={idEntity}
    )
    SELECT
        queue.refdate AS Refdate,
        queue.entity AS IdEntity,
        entity.name AS Entity,
        queue.budgetyear AS BudgetYear,
        productcourt.name AS Court,
        queue.receivedat AS ReceivedAt,
        queue.budgetyear AS Year,
        productspecification.name AS Type,
        queue.queueposition AS QueuePosition,
        queue.codeproduct AS Id,
        queue.value AS Value
    FROM
        queue
    LEFT JOIN productcourt ON productcourt.id = queue.court
    LEFT JOIN productspecification ON queue.specification = productspecification.id
    LEFT JOIN entity ON queue.entity = entity.id
    WHERE
        queue.entity={idEntity}
        AND queue.refdate=(SELECT MAX(Refdate) FROM refdateTable)
    ORDER BY
        QueuePosition
    """
    
    return query

def queryEntityMap(idEntity):

    query = f"""
    WITH entityMapExercicio AS (
        SELECT DISTINCT
            entitymap.exercicio AS Exercicio
        FROM
            entitymap
        WHERE
            entitymap.entity={idEntity}
    )
    SELECT
        *
    FROM
        entitymap
    WHERE
        entitymap.entity={idEntity}
        AND exercicio=(SELECT MAX(Exercicio) FROM entityMapExercicio)
    """

    return query

def queryEntityRegime(idEntity):

    query = f"""
    WITH regimeDates AS (
        SELECT DISTINCT
            refdate
        FROM
            regime
        WHERE 
            entity={idEntity}
    )
    SELECT
        regime.entity AS IdEntity,
        regime.regimeType AS IdRegime,
        regimetype.name AS Regime
    FROM
        regime
    LEFT JOIN regimeType ON regime.regimetype=regimetype.id
    WHERE
        regime.refdate=(SELECT MAX(refdate) FROM regimeDates)
        AND regime.entity={idEntity}
    """

    return query

def queryEntityStats(idEntity):

    query = f"""
    WITH entityStatsYears AS (
        SELECT DISTINCT
            exercicio
        FROM
            entitystats
        WHERE
            entity={idEntity}
    )
    SELECT
        *
    FROM
        entitystats
    WHERE
        entitystats.entity={idEntity}
        AND entitystats.exercicio=(SELECT MAX(exercicio) FROM entityStatsYears)
        AND entitystats.coluna='{RCL_FIELD}'
    """

    return query

def queryEntityPlan(idEntity):
    
    query = f"""
    WITH entityPlanExercicio AS (
        SELECT DISTINCT
            exercicio
        FROM
            entityplan
        WHERE
            entity={idEntity}
    )
    SELECT
        *
    FROM
        entityplan
    WHERE
        entityplan.entity={idEntity}
        AND entityplan.exercicio=(SELECT MAX(exercicio) FROM entityPlanExercicio)
    """

    return query

def queryEntityDeal(idEntity):
    
    query = f"""
    SELECT 
        entitydeal.id AS id,
        entitydeal.entity as entity,
        entitydeal.name as name,
        entitydeal.acordo as acordo,
        entitydeal.obsacordo as obsacordo,
        entitydeal.compensacao as compensacao,
        entitydeal.rpv as rpv,
        entitydeal.pctacordo as pctacordo,
        entitydeal.pctdesagiomin as pctdesagiomin,
        entitydeal.pctdesagiomax as pctdesagiomax,
        entitydeal.termosacordo as termosacordo,
        entitydeal.contagemeditais as contagemeditais,
        entitydeal.prazoesperadoparapagamento as prazoesperadoparapagamento,
        entitydeal.montantemedioderecursosporedital as montantemedioderecursosporedital,
        entitydealstatustype.name as dealfrequencia
    FROM 
        entitydeal
    LEFT JOIN entitydealstatustype ON entitydealstatustype.id=entitydeal.statusfrequencia
    WHERE
        entitydeal.entity={idEntity}
    """

    return query