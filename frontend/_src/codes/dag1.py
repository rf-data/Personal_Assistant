def _any_file_exists(**context):
    folder = DATA_INPUT
    files = [str(f) for f in folder.iterdir()
             if f.suffix.lower() in types_allowed]
    
    return bool(files) #  if files else False

# defining DAG
@dag(
    dag_id="data_processing_pipeline", 
    tags=["franke", "rakuten", "recommender"],
    schedule_interval="@monthly",
    start_date=datetime(2025, 12, 4),
    catchup=False,
    default_args={
        "retries": 1,
        "retry_delay": timedelta(seconds=10)
    }
)

def data_processing_pipeline():

    # sensor checks for new files 
    wait_for_file = PythonSensor(
            task_id="wait_for_file",
            python_callable = _any_file_exists, 
            poke_interval=10,
            timeout=60 * 60,   
            mode="poke"
    )
            
    # task 1: 
    @task
    def run_fetch_files():
        files = fetch_files(src_path=DATA_INPUT, 
                            dst_path=DATA_LAKE)
        if not files:
            raise AirflowSkipException("During 'run_fetch_files', no files found")

        return [str(f) for f in files]
    
    # task 2: check content of new files 
    @task
    def run_new_file_check(files):
        check_result = new_file_check(f_names=files, 
                                      folder=DATA_LAKE)
        return check_result

    # task 3-A: ETL text  
    @task
    def run_text_general_etl(files, check_result):
        return text_general_etl(f_names=files, 
                            src_folder=DATA_LAKE, 
                            dst_folder=DATA_DONE,
                            product_dict=check_result)

    # task 3-B: ETL image  
    @task
    def run_image_etl(check_result):
        result = image_etl(img_path=DATA_LAKE, 
                            dst_folder=DATA_DONE,
                            product_dict=check_result)
        
        status = result.get("status", "unknown")

        if status == "skipped":
            print("Skipped 'file unzipping' – destination folder ist not empty")
        
        else: 
            return result

    # task 4-A: create embeddings from text
    @task
    def run_text_embed(_):
        return text_embed()

    @task
    def run_image_embed(_):
        return image_embed()
    # task 4-B: create embeddings from text
    # @task
    # def run_image_embed(_):
    #     return image_embed()

    # define dependencies
    fetched = run_fetch_files()
    check_result = run_new_file_check(fetched)

    etl_text = run_text_general_etl(fetched, check_result)
    etl_image = run_image_etl(check_result)
    
    run_text_embed(etl_text)
    run_image_embed(etl_image)
    
    wait_for_file >> fetched



pipeline = data_processing_pipeline()
